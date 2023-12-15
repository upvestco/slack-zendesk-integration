
#Slack app title
title = "{title}"

#Slack app inside logo
logo = "{path to logo}"

#Zendesk API Endpoint
domain = "https://{your domain}.zendesk.com"

#Zendesk group abbreviations, as many as needed, below are examples
group_operations = "OPS"
group_legal = "LEGAL"
group_support = "TECH"

#ID of the custom field that holds owning team for ticket creation
owning_team_field_id = "some-field-id"

#Operation types + subtypes
operation = [
    {
        "text":"Tax",
        "value":"type_tax",
        "group": group_operations,
        "sub": [
            "Client ID/User ID", 
            "Account ID and name",
            "Transaction ID",
            "Shares/Amount",
        ]
    },
    {
        "text":"User and Accounts",
        "value":"type_user_and_accounts",
        "group": group_operations,
        "sub": [
            "Client ID/User ID",
            "Account ID and name",
        ]
    },
    {
        "text":"Payments",
        "value":"type_payments",
        "group": group_operations,
        "sub": [
            "Amount",
            "Value date/date of transfer",
            "Mode of transfer"
        ]
    },
    {
        "text":"Portfolios",
        "value":"type_portfolios",
        "group": group_operations,
        "sub": [
            "Portfolio ID",
            "TD/VD",
            "Shares/Amount",
            "User ID",
        ]
    },
    {
        "text":"Orders",
        "value":"type_orders",
        "group": group_operations,
        "sub": [
            "ISIN",
            "TD/VD",
            "Price",
            "Shares",
            "Amount",
            "Order ID",
        ]
    },
    {
        "text":"Positions",
        "value":"type_positions",
        "group": group_operations,
        "sub": [
            "ISIN",
            "Shares/Amount",
            "Client ID/User ID",
        ]
    },
    {
        "text":"Instruments",
        "value":"type_instruments",
        "group": group_operations,
        "sub": [
            "ISIN/VKN",
            "Country/Market",
        ]
    },
    {
        "text":"Reports",
        "value":"type_reports",
        "group": group_operations,
        "sub": [
            "Client ID/User ID",
            "Account ID and name",
            "Report ID and name",
        ]
    },
    {
        "text":"Corporate Actions",
        "value":"type_corporate_actions",
        "group": group_operations,
        "sub": [
            "ISIN",
            "Event type (e.g. Dividend Payment/Merger or DVCA/MRGR)",
            "Name",
        ]
    },
    {
        "text":"Complaints",
        "value":"type_complaints",
        "group": group_legal,
        "sub": []
    }
]

#Technical types + subtypes
technical = [
    {
        "text":"API request issue",
        "value":"type_api_request_issue",
        "group": group_support,
        "sub": [
            "Request ID"
        ]
    },
    {
        "text":"Webhooks issue",
        "value":"type_webhooks_issue",
        "group": group_support,
        "sub": [
            "Subscription ID",
            "Webhooks subscription type",
        ]
    },
    {
        "text":"Other",
        "value":"type_other",
        "group": group_support,
        "sub": []
    }
]
