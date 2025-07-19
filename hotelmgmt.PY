import mysql.connector
from mysql.connector import errorcode
# --- IMPORT YOUR CONFIGURATION ---
# This line imports the MYSQL_CONFIG dictionary from your private config.py file.
from config import MYSQL_CONFIG

# --- MySQL Configuration ---
DB_NAME = 'hotel_db'
# The MYSQL_CONFIG dictionary is now safely in a separate file.

def setup_database():
    """Connects to MySQL, creates the database and table if they don't exist."""
    try:
        # Connect to the MySQL server first
        server_conn = mysql.connector.connect(
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            host=MYSQL_CONFIG['host'],
            charset='utf8'
        )
        cursor = server_conn.cursor()
        
        # Create the database if it doesn't exist
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DB_CREATE_EXISTS:
                pass # Database already exists, which is fine.
            else:
                raise err
        
        cursor.close()
        server_conn.close()

        # Connect to the specific database
        db_conn = mysql.connector.connect(**MYSQL_CONFIG, database=DB_NAME, charset='utf8')
        cursor = db_conn.cursor()
        
        # We will only create the table if it doesn't exist.
        print("Ensuring 'customers' table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                contact VARCHAR(20) NOT NULL,
                address TEXT NOT NULL,
                room_number INT NOT NULL UNIQUE,
                check_in_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Database and table are ready.")
        cursor.close()
        return db_conn

    except mysql.connector.Error as err:
        print(f"Database setup error: {err}")
        return None

# --- Core Functionality ---

def check_in_customer(conn):
    """Prompts for new customer details and adds them to the database."""
    print("\n--- New Customer Check-In ---")
    try:
        name = input("Enter customer's full name: ")
        contact = input("Enter contact number: ")
        address = input("Enter address: ")
        room_number = int(input("Enter allocated room number: "))

        if not all([name, contact, address, room_number]):
            print("Error: All fields are required.")
            return

        cursor = conn.cursor()
        sql = "INSERT INTO customers (name, contact, address, room_number) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, contact, address, room_number))
        conn.commit()
        print(f"\nSuccess! Customer '{name}' checked into room {room_number}.")
        cursor.close()

    except ValueError:
        print("\nInvalid input. Room number must be an integer.")
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry
            print(f"\nError: Room number '{room_number}' is already in use.")
        else:
            print(f"An error occurred: {err}")

def view_all_customers(conn):
    """Retrieves and displays all customer records."""
    print("\n--- All Checked-In Customers ---")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact, room_number, check_in_date FROM customers ORDER BY room_number")
        customers = cursor.fetchall()

        if not customers:
            print("No customers are currently checked in.")
            cursor.close()
            return

        print(f"{'ID':<5} | {'Name':<25} | {'Contact':<15} | {'Room No.':<10} | {'Check-In Date':<20}")
        print("-" * 85)
        for customer in customers:
            check_in_str = customer[4].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{customer[0]:<5} | {customer[1]:<25} | {customer[2]:<15} | {customer[3]:<10} | {check_in_str:<20}")
        cursor.close()

    except mysql.connector.Error as err:
        print(f"An error occurred while fetching data: {err}")

def find_customer(conn):
    """Finds and displays a specific customer by room number."""
    print("\n--- Find a Customer ---")
    try:
        room_number = int(input("Enter the room number to find: "))
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact, address, room_number, check_in_date FROM customers WHERE room_number = %s", (room_number,))
        customer = cursor.fetchone()

        if customer:
            print("\nCustomer Found:")
            print("-" * 20)
            print(f"  ID: {customer[0]}")
            print(f"  Name: {customer[1]}")
            print(f"  Contact: {customer[2]}")
            print(f"  Address: {customer[3]}")
            print(f"  Room Number: {customer[4]}")
            print(f"  Check-In Date: {customer[5].strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 20)
        else:
            print(f"No customer found in room number {room_number}.")
        cursor.close()
    except ValueError:
        print("Invalid input. Please enter a valid room number.")
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")

def check_out_customer(conn):
    """Deletes a customer's record based on room number."""
    print("\n--- Customer Check-Out ---")
    try:
        room_number = int(input("Enter room number for check-out: "))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM customers WHERE room_number = %s", (room_number,))
        customer_name = cursor.fetchone()

        if not customer_name:
            print(f"Error: Room {room_number} is not occupied.")
            cursor.close()
            return

        confirm = input(f"Check out customer '{customer_name[0]}' from room {room_number}? (y/n): ").lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM customers WHERE room_number = %s", (room_number,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Success! Customer from room {room_number} has been checked out.")
            else:
                print("Could not process check-out.")
        else:
            print("Check-out cancelled.")
        cursor.close()
    except ValueError:
        print("Invalid input. Please enter a valid room number.")
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")

# --- Main Application Logic ---
def main():
    """The main function to run the command-line interface."""
    conn = setup_database()
    if not conn:
        print("Exiting due to database connection failure.")
        return

    while True:
        print("\n===================================")
        print("   Hotel Management System Menu")
        print("===================================")
        print("1. Check-In New Customer")
        print("2. View All Customers")
        print("3. Find a Customer")
        print("4. Check-Out Customer")
        print("5. Exit")
        print("-----------------------------------")
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            check_in_customer(conn)
        elif choice == '2':
            view_all_customers(conn)
        elif choice == '3':
            find_customer(conn)
        elif choice == '4':
            check_out_customer(conn)
        elif choice == '5':
            print("Exiting the system. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option.")

    if conn and conn.is_connected():
        conn.close()
        print("MySQL connection is closed.")

if __name__ == '__main__':
    main()
