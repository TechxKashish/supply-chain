from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "data.db"

SCHEMA = """
DATABASE TABLES AND EXACT COLUMN NAMES:

1. sales_order_headers
   - salesOrder (PK), soldToParty, totalNetAmount, overallDeliveryStatus, 
     overallOrdReltdBillgStatus, creationDate, salesOrderType, transactionCurrency

2. sales_order_items
   - salesOrder (FK), salesOrderItem, material, requestedQuantity, netAmount, materialGroup

3. sales_order_schedule_lines
   - salesOrder, salesOrderItem, scheduleLine, confirmedDeliveryDate

4. outbound_delivery_headers
   - deliveryDocument (PK), overallGoodsMovementStatus, overallPickingStatus, 
     creationDate, shippingPoint, headerBillingBlockReason

5. outbound_delivery_items
   - deliveryDocument (FK), deliveryDocumentItem, plant, 
     referenceSdDocument (= salesOrder), referenceSdDocumentItem, actualDeliveryQuantity

6. billing_document_headers
   - billingDocument (PK), soldToParty, totalNetAmount, 
     billingDocumentIsCancelled, accountingDocument, billingDocumentDate

7. billing_document_items
   - billingDocument (FK), billingDocumentItem, material, netAmount, 
     referenceSdDocument (= deliveryDocument), referenceSdDocumentItem

8. billing_document_cancellations
   - billingDocument, billingDocumentIsCancelled, cancelledBillingDocument, totalNetAmount

9. journal_entry_items_accounts_receivable
   - accountingDocument, referenceDocument (= billingDocument), customer, 
     amountInTransactionCurrency, postingDate, clearingAccountingDocument

10. payments_accounts_receivable
    - accountingDocument, customer, amountInTransactionCurrency, 
      clearingAccountingDocument, postingDate, invoiceReference

11. business_partners
    - businessPartner (PK), customer (= soldToParty), businessPartnerFullName, 
      businessPartnerIsBlocked, creationDate

12. business_partner_addresses
    - businessPartner, cityName, country, streetName, postalCode, region

13. customer_company_assignments
    - customer, companyCode, paymentTerms, reconciliationAccount

14. customer_sales_area_assignments
    - customer, salesOrganization, distributionChannel, currency, customerPaymentTerms

15. products
    - product (PK), productType, productGroup, grossWeight, baseUnit, division

16. product_descriptions
    - product (FK), language, productDescription

17. product_plants
    - product, plant, profitCenter, mrpType

18. product_storage_locations
    - product, plant, storageLocation

19. plants
    - plant (PK), plantName, salesOrganization, addressId, distributionChannel

KEY RELATIONSHIPS (use these for JOINs):
- sales_order_headers.soldToParty = business_partners.customer
- sales_order_headers.soldToParty = business_partners.businessPartner
- sales_order_items.salesOrder = sales_order_headers.salesOrder
- sales_order_items.material = products.product
- products.product = product_descriptions.product
- outbound_delivery_items.referenceSdDocument = sales_order_headers.salesOrder
- outbound_delivery_items.deliveryDocument = outbound_delivery_headers.deliveryDocument
- billing_document_items.referenceSdDocument = outbound_delivery_headers.deliveryDocument
- billing_document_items.billingDocument = billing_document_headers.billingDocument
- billing_document_items.material = products.product
- billing_document_headers.accountingDocument = journal_entry_items_accounts_receivable.accountingDocument
- billing_document_headers.accountingDocument = payments_accounts_receivable.accountingDocument
- journal_entry_items_accounts_receivable.referenceDocument = billing_document_headers.billingDocument

COMMON QUERY PATTERNS:
- Full flow trace: sales_order_headers → outbound_delivery_items → billing_document_items → billing_document_headers → payments_accounts_receivable
- Products with most billing docs: JOIN billing_document_items with product_descriptions ON material = product, GROUP BY material, COUNT billingDocument
- Sales orders with no invoice: LEFT JOIN sales_order_headers with billing_document_items ON salesOrder = referenceSdDocument WHERE billingDocument IS NULL
- Unbilled deliveries: LEFT JOIN outbound_delivery_headers with billing_document_items ON deliveryDocument = referenceSdDocument WHERE billingDocument IS NULL
- Customer order totals: JOIN sales_order_headers with business_partners ON soldToParty = customer
- Cancelled invoices: SELECT from billing_document_cancellations WHERE billingDocumentIsCancelled = 'True'
- Payments received: SELECT from payments_accounts_receivable JOIN billing_document_headers ON accountingDocument
"""

SYSTEM_PROMPT = f"""
You are an expert SQLite query generator for a supply chain database.
You must answer ANY question related to this supply chain data.

{SCHEMA}

STRICT RULES:
- Return ONLY a valid SQLite SQL query, absolutely nothing else
- No markdown, no backticks, no explanation, no comments
- Only SELECT statements — never DROP/DELETE/INSERT/UPDATE/ALTER
- Always wrap table names in double quotes: "table_name"
- Always wrap column names in double quotes when ambiguous
- LIMIT 20 rows unless user asks for more
- For counting/aggregation questions always use GROUP BY + ORDER BY COUNT DESC
- For trace questions use multiple LEFT JOINs to show full flow
- For yes/no existence questions use COUNT(*)
- If question is completely unrelated to supply chain data (e.g. cooking, sports, weather), return exactly: OUT_OF_SCOPE
- For ANY question about orders, products, customers, deliveries, invoices, payments, billing — always attempt a query
"""

SUMMARY_PROMPT = """
You are a supply chain data analyst. Answer clearly and concisely.
The user asked: {question}

Data returned:
{results}

Rules:
- Maximum 3 sentences or 4 bullet points
- Use plain text only, no asterisks, no markdown, no special characters
- Start bullet points with a dash: - 
- Be direct with numbers and IDs
- No filler phrases like "the data shows" or "based on results"
"""

OFF_TOPIC_KEYWORDS = [
    "poem", "recipe", "weather", "capital of", "who invented",
    "movie", "song", "joke", "write a story", "history of",
    "how to cook", "sports", "cricket", "football", "politics"
]

def query_db(sql: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

def get_graph_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    nodes = []
    edges = []
    node_ids = set()

    def add_node(node_id, label, node_type, props={}):
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type,
                "properties": props
            })

    cursor.execute('SELECT salesOrder, soldToParty, totalNetAmount, overallDeliveryStatus FROM "sales_order_headers" LIMIT 30')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"SO_{row['salesOrder']}"
        add_node(nid, f"Order\n{row['salesOrder']}", "SalesOrder", row)

    cursor.execute('SELECT businessPartner, businessPartnerFullName, customer FROM "business_partners" LIMIT 20')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"BP_{row['businessPartner']}"
        add_node(nid, f"Customer\n{row['businessPartnerFullName'][:15]}", "Customer", row)

    cursor.execute('SELECT deliveryDocument, overallGoodsMovementStatus, overallPickingStatus FROM "outbound_delivery_headers" LIMIT 30')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"DEL_{row['deliveryDocument']}"
        add_node(nid, f"Delivery\n{row['deliveryDocument']}", "Delivery", row)

    cursor.execute('SELECT billingDocument, totalNetAmount, billingDocumentIsCancelled, soldToParty FROM "billing_document_headers" LIMIT 30')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"BILL_{row['billingDocument']}"
        add_node(nid, f"Invoice\n{row['billingDocument']}", "Billing", row)

    cursor.execute('''
        SELECT p.product, pd.productDescription
        FROM "products" p
        LEFT JOIN "product_descriptions" pd ON p.product = pd.product
        LIMIT 20
    ''')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"PROD_{row['product']}"
        label = row['productDescription'] or row['product']
        add_node(nid, f"Product\n{label[:15]}", "Product", row)

    cursor.execute('SELECT accountingDocument, customer, amountInTransactionCurrency FROM "payments_accounts_receivable" LIMIT 20')
    for row in cursor.fetchall():
        row = dict(row)
        nid = f"PAY_{row['accountingDocument']}"
        add_node(nid, f"Payment\n{row['accountingDocument']}", "Payment", row)

    cursor.execute('SELECT salesOrder, soldToParty FROM "sales_order_headers" LIMIT 30')
    for row in cursor.fetchall():
        src = f"BP_{row['soldToParty']}"
        tgt = f"SO_{row['salesOrder']}"
        if src in node_ids and tgt in node_ids:
            edges.append({"from": src, "to": tgt, "label": "PLACED"})

    cursor.execute('SELECT DISTINCT referenceSdDocument, deliveryDocument FROM "outbound_delivery_items" LIMIT 30')
    for row in cursor.fetchall():
        src = f"SO_{row['referenceSdDocument']}"
        tgt = f"DEL_{row['deliveryDocument']}"
        if src in node_ids and tgt in node_ids:
            edges.append({"from": src, "to": tgt, "label": "DELIVERED_VIA"})

    cursor.execute('SELECT DISTINCT referenceSdDocument, billingDocument FROM "billing_document_items" LIMIT 30')
    for row in cursor.fetchall():
        src = f"DEL_{row['referenceSdDocument']}"
        tgt = f"BILL_{row['billingDocument']}"
        if src in node_ids and tgt in node_ids:
            edges.append({"from": src, "to": tgt, "label": "BILLED_AS"})

    cursor.execute('SELECT accountingDocument, referenceDocument FROM "journal_entry_items_accounts_receivable" LIMIT 30')
    for row in cursor.fetchall():
        src = f"BILL_{row['referenceDocument']}"
        tgt = f"PAY_{row['accountingDocument']}"
        if src in node_ids and tgt in node_ids:
            edges.append({"from": src, "to": tgt, "label": "PAID_VIA"})

    cursor.execute('SELECT salesOrder, material FROM "sales_order_items" LIMIT 30')
    for row in cursor.fetchall():
        src = f"SO_{row['salesOrder']}"
        tgt = f"PROD_{row['material']}"
        if src in node_ids and tgt in node_ids:
            edges.append({"from": src, "to": tgt, "label": "INCLUDES"})

    conn.close()
    return {"nodes": nodes, "edges": edges}


class ChatRequest(BaseModel):
    message: str


@app.get("/api/graph")
def get_graph():
    return get_graph_data()


@app.post("/api/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()

    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword.lower() in user_message.lower():
            return {"response": "This system is designed to answer questions related to the supply chain dataset only."}

    if len(user_message) < 5:
        return {"response": "Please ask a question about the supply chain data."}

    try:
        sql_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": SYSTEM_PROMPT + "\n\nQuestion: " + user_message}]
        )
        sql = sql_response.choices[0].message.content.strip()

        if sql == "OUT_OF_SCOPE":
            return {"response": "This system is designed to answer questions related to the supply chain dataset only."}

        for dangerous in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER"]:
            if dangerous in sql.upper():
                return {"response": "Invalid query. Only data retrieval questions are supported."}

        results = query_db(sql)

        if isinstance(results, dict) and "error" in results:
            return {"response": "Could not retrieve data. Please rephrase your question.", "sql": sql}

        if not results:
            return {"response": "No data found for your query. Try rephrasing or ask about a different entity.", "sql": sql}

        summary_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(question=user_message, results=str(results[:10]))}]
        )
        return {
            "response": summary_response.choices[0].message.content.strip(),
            "sql": sql,
            "data": results[:10]
        }

    except Exception as e:
        return {"response": f"Error: {str(e)}"}
    
from fastapi.responses import FileResponse

@app.get("/vis-network.min.js")
def serve_vis():
    return FileResponse("vis-network.min.js")
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()