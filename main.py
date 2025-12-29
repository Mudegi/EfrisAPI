import os
from efris_client import EfrisManager

# Example usage
def main():
    print("Starting main")
    client = EfrisManager(tin='1015264035', test_mode=True)  # Set to True for test environment

    # Example: Get registration details
    try:
        details = client.get_registration_details()
        print('Registration Details:', details)
    except Exception as e:
        print('Error:', e)

    # Example: Issue receipt (sample data)
    # receipt_data = {
    #     'buyerTin': '1015264035',
    #     'buyerName': 'John Doe',
    #     'deviceId': '1015264035_04',  # Device number
    #     'items': [
    #         {
    #             'itemCode': '001',
    #             'itemName': 'Item 1',
    #             'quantity': 1,
    #             'unitPrice': 100.0,
    #             'taxRate': 18.0
    #         }
    #     ],
    #     'totalAmount': 118.0
    # }
    # try:
    #     receipt = client.issue_receipt(receipt_data)
    #     print('Receipt:', receipt)
    # except Exception as e:
    #     print('Error:', e)

if __name__ == '__main__':
    main()