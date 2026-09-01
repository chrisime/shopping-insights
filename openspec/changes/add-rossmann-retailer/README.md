# add-rossmann-retailer

Add Rossmann as a retailer: digital receipts are served by the anybill App API v4; the Rossmann app mints an anybill token via account.ws (accounts/{accountId}/receipt/auth), then fetches receipts from app.anybill.de/api/v4/receipt.
