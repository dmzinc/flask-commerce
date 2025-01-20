import plantuml
import os

def generate_diagrams():
    # Create directories
    os.makedirs('docs/diagrams', exist_ok=True)
    
    # Sequence diagram content
    sequence_content = """
@startuml return_exchange_sequence
actor Customer
participant "API" as API
participant "Order" as Order
participant "Return/Exchange" as RetEx
participant "Admin" as Admin

Customer -> API: POST /orders/return or /orders/exchange
activate API
API -> Order: Validate purchase
activate Order
Order --> API: Purchase validated
deactivate Order
API -> RetEx: Create request
activate RetEx
RetEx -> RetEx: process()
RetEx --> API: Request created
deactivate RetEx
API --> Customer: Confirmation & ID
deactivate API
Admin -> API: POST /orders/{id}/approve
activate API
API -> RetEx: Update status
API --> Admin: Confirmation
deactivate API
@enduml
"""

    # Class diagram content
    class_content = """
@startuml ecommerce_class_diagram
abstract class Order {
  +id: Integer
  +user_id: Integer
  +product_id: Integer
  +date: DateTime
  +status: String
  +type: String
  +quantity: Integer
  +total_price: Float
  +{abstract} process()
  +get_details()
}

class Purchase {
  +shipping_address: String
  +payment_method: String
  +process()
}

class Cart {
  +process()
  +check_stock()
  +to_dict()
}

class Return {
  +reason: String
  +refund_amount: Float
  +customer_email: String
  +customer_name: String
  +purchase_date: DateTime
  +original_purchase_id: Integer
  +admin_notes: String
  +process()
}

class Exchange {
  +new_product_id: Integer
  +reason: String
  +customer_email: String
  +customer_name: String
  +purchase_date: DateTime
  +original_purchase_id: Integer
  +admin_notes: String
  +process()
}

class User {
  +id: Integer
  +email: String
  +role: String
  +authenticate()
  +get_orders()
}

class Product {
  +id: Integer
  +name: String
  +price: Float
  +description: String
  +get_details()
}

class PhysicalProduct {
  +weight: Float
  +stock: Integer
  +check_stock()
}

class DigitalProduct {
  +file_size: Float
  +download_link: String
  +generate_download_link()
}

Order <|-- Purchase
Order <|-- Cart
Order <|-- Return
Order <|-- Exchange

Product <|-- PhysicalProduct
Product <|-- DigitalProduct

Order "*" -- "1" User: placed by >
Order "*" -- "1" Product: contains >
Cart "*" -- "*" Product: contains >
@enduml
"""

    # State diagram content
    state_content = """
@startuml order_state_diagram
[*] --> Cart: Add to Cart
Cart --> Completed: Complete Purchase
Completed --> PendingApproval: Request Return/Exchange
PendingApproval --> Approved: Admin Approves
PendingApproval --> Rejected: Admin Rejects
Approved --> [*]
Rejected --> [*]
@enduml
"""

    # Write diagram contents to files
    diagrams = {
        'sequence_diagram.puml': sequence_content,
        'class_diagram.puml': class_content,
        'state_diagram.puml': state_content
    }

    for filename, content in diagrams.items():
        with open(f'docs/diagrams/{filename}', 'w') as f:
            f.write(content)

    # Create PlantUML instance
    pu = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

    # Generate all diagrams
    for diagram in diagrams.keys():
        try:
            input_file = f'docs/diagrams/{diagram}'
            output_file = f'docs/diagrams/{diagram.replace(".puml", ".png")}'
            pu.processes_file(input_file, outfile=output_file)
            print(f"Generated {diagram.replace('.puml', '.png')}")
        except Exception as e:
            print(f"Error generating {diagram}: {str(e)}")

if __name__ == '__main__':
    generate_diagrams()
    print("All diagrams generated successfully in docs/diagrams/")