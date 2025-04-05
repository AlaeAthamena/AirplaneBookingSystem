import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import random
import string
import sqlite3
import os


class SeatBookingSystem:
    def __init__(self):
        self.num_rows = 7
        self.num_cols = 80
        # Initialize seats with type information (tuple: status, seat_type, booking_reference)
        self.seats = [[('F', 'Economy', None) for _ in range(self.num_cols)] for _ in range(self.num_rows)]
        self.row_letters = 'ABCDEFG'
        self.mark_special_seats()
        self.selected_seats = set()  # Store multiple selected seats
        self.booking_references = set()  # Store unique booking references

        # Initialize database
        self.initialize_database()

        # Load existing bookings from database
        self.load_bookings_from_database()

        # Define seat types and their colors
        self.seat_types = {
            'Economy': 'white',
            'First': 'white',  # Same base color, will use border to differentiate
            'Storage': 'lightgray',
            'Aisle': 'gray'
        }

    def initialize_database(self):
        """Initialize SQLite database to store booking information"""
        # Create a connection to the database (or create if it doesn't exist)
        self.conn = sqlite3.connect('airline_bookings.db')
        self.cursor = self.conn.cursor()

        # Create bookings table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_reference TEXT PRIMARY KEY,
            passport_number TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
        ''')

        # Create seats table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS booked_seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_reference TEXT NOT NULL,
            seat_row TEXT NOT NULL,
            seat_column INTEGER NOT NULL,
            seat_type TEXT NOT NULL,
            FOREIGN KEY (booking_reference) REFERENCES bookings (booking_reference)
        )
        ''')

        self.conn.commit()

        # Load existing booking references
        self.cursor.execute("SELECT booking_reference FROM bookings")
        existing_references = self.cursor.fetchall()
        for ref in existing_references:
            self.booking_references.add(ref[0])

    def load_bookings_from_database(self):
        """Load all existing bookings from database into the seats array"""
        try:
            # Query all booked seats
            self.cursor.execute("""
            SELECT booking_reference, seat_row, seat_column, seat_type 
            FROM booked_seats
            """)

            booked_seats = self.cursor.fetchall()

            # Update seat status in the system
            for booking_ref, row_letter, col_num, seat_type in booked_seats:
                # Convert row letter to index
                row_idx = self.row_letters.index(row_letter)
                # Column is 1-indexed in the database but 0-indexed in our array
                col_idx = col_num - 1

                if 0 <= row_idx < self.num_rows and 0 <= col_idx < self.num_cols:
                    # Mark seat as reserved with the booking reference
                    self.seats[row_idx][col_idx] = (booking_ref, seat_type, booking_ref)
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def mark_special_seats(self):
        """Marks special seats and their types in the seating layout"""
        # Mark row D as aisle
        for col in range(self.num_cols):
            self.seats[3][col] = ('A', 'Aisle', None)  # Changed 'X' to 'A' for Aisle

        # Storage columns
        storage_columns = [13, 14, 15, 28, 29, 30, 43, 44, 45, 58, 59, 60, 73, 74, 75]
        for col in storage_columns:
            for row in range(self.num_rows):
                if row != 3:
                    self.seats[row][col] = ('S', 'Storage', None)

        # Set First Class seats (columns 1-30)
        for col in range(30):
            for row in range(self.num_rows):
                if self.seats[row][col][0] == 'F':
                    self.seats[row][col] = ('F', 'First', None)

    def get_seat_name(self, row, col):
        return f"{self.row_letters[row]}{col + 1}"

    def toggle_seat_selection(self, row, col):
        """Toggle seat selection for bulk booking"""
        seat_pos = (row, col)
        status, seat_type, _ = self.seats[row][col]

        # Only allow selection of free seats or those with booking references (reserved)
        if status not in ['F'] and not self.is_booking_reference(status):
            return False, None  # Return None to indicate no selection change

        if seat_pos in self.selected_seats:
            self.selected_seats.remove(seat_pos)
            return True, f"Unselected seat {self.get_seat_name(row, col)}"
        else:
            self.selected_seats.add(seat_pos)
            return True, f"Selected seat {self.get_seat_name(row, col)}"

    def is_booking_reference(self, status):
        """Check if a status string is likely a booking reference (8 alphanumeric characters)"""
        return isinstance(status, str) and len(status) == 8 and all(
            c in string.ascii_uppercase + string.digits for c in status)

    def book_seats(self, passenger_info=None, priority_booking=False):
        """Book multiple selected seats with passenger information"""
        if not self.selected_seats:
            return False, "No seats selected"

        # If passenger_info is not provided, return early
        if not passenger_info:
            return False, "Passenger information is required"

        passport_number, first_name, last_name = passenger_info

        # Generate a new booking reference
        booking_reference = self.generate_booking_reference()

        # Store traveler details in database
        try:
            # Insert booking information
            self.cursor.execute('''
            INSERT INTO bookings (booking_reference, passport_number, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ''', (booking_reference, passport_number, first_name, last_name))

            # Book all selected seats
            booked_seats = []
            for row, col in self.selected_seats:
                status, seat_type, _ = self.seats[row][col]
                if status == 'F':  # Only book if seat is free
                    # Update in-memory seat representation
                    self.seats[row][col] = (booking_reference, seat_type, booking_reference)

                    # Store seat information in database
                    self.cursor.execute('''
                    INSERT INTO booked_seats (booking_reference, seat_row, seat_column, seat_type)
                    VALUES (?, ?, ?, ?)
                    ''', (booking_reference, self.row_letters[row], col + 1, seat_type))

                    booked_seats.append(self.get_seat_name(row, col))

            # Commit database changes
            self.conn.commit()

            self.selected_seats.clear()
            return True, f"Booked seats: {', '.join(booked_seats)} for {first_name} {last_name}. Reference: {booking_reference}"

        except sqlite3.Error as e:
            # Roll back on error
            self.conn.rollback()
            return False, f"Database error: {str(e)}"

    def free_seats(self):
        """Free multiple selected seats"""
        if not self.selected_seats:
            return False, "No seats selected"

        freed_seats = []
        booking_refs_to_check = set()

        try:
            for row, col in self.selected_seats:
                status, seat_type, booking_ref = self.seats[row][col]
                if self.is_booking_reference(status):  # Check if it's a booking reference
                    booking_refs_to_check.add(status)

                    # Update seat in memory
                    self.seats[row][col] = ('F', seat_type, None)

                    # Delete seat from database
                    self.cursor.execute('''
                    DELETE FROM booked_seats 
                    WHERE booking_reference = ? AND seat_row = ? AND seat_column = ?
                    ''', (status, self.row_letters[row], col + 1))

                    freed_seats.append(self.get_seat_name(row, col))

            # For each booking reference, check if any seats remain
            for ref in booking_refs_to_check:
                self.cursor.execute('SELECT COUNT(*) FROM booked_seats WHERE booking_reference = ?', (ref,))
                count = self.cursor.fetchone()[0]

                # If no seats remain, delete the booking entry
                if count == 0:
                    self.cursor.execute('DELETE FROM bookings WHERE booking_reference = ?', (ref,))
                    self.booking_references.remove(ref)

            # Commit database changes
            self.conn.commit()

            self.selected_seats.clear()
            return True, f"Freed seats: {', '.join(freed_seats)}"

        except sqlite3.Error as e:
            # Roll back on error
            self.conn.rollback()
            return False, f"Database error: {str(e)}"

    def get_seat_status(self, row, col):
        """Get the status of a specific seat"""
        if not (0 <= row < self.num_rows and 0 <= col < self.num_cols):
            return "Invalid seat position"

        status, seat_type, booking_reference = self.seats[row][col]
        seat_name = self.get_seat_name(row, col)

        # Check if status is actually a booking reference
        if self.is_booking_reference(status):
            # Query passenger information from database
            try:
                self.cursor.execute('''
                SELECT passport_number, first_name, last_name
                FROM bookings
                WHERE booking_reference = ?
                ''', (status,))

                result = self.cursor.fetchone()
                if result:
                    passport_number, first_name, last_name = result
                    return f"Seat {seat_name} is Reserved ({seat_type} Class). " \
                           f"Booking Reference: {status}, " \
                           f"Passenger: {first_name} {last_name}, " \
                           f"Passport: {passport_number}"
            except sqlite3.Error:
                pass

            return f"Seat {seat_name} is Reserved ({seat_type} Class). Reference: {status}"
        else:
            status_map = {
                'F': 'Free',
                'A': 'Aisle',
                'S': 'Storage'
            }
            status_text = status_map.get(status, 'Unknown')
            return f"Seat {seat_name} is {status_text} ({seat_type} Class)"

    def generate_booking_reference(self):
        """
        Generate a unique random booking reference with 8 alphanumeric characters.

        This algorithm works as follows:
        1. Create a random 8-character string using uppercase letters and digits
        2. Check if this reference already exists in our set of booking references
        3. If it exists, generate a new one until we find a unique reference
        4. Add the new reference to our set and return it

        Using a set data structure ensures O(1) lookup time when checking for duplicates,
        making this algorithm efficient even with many existing bookings.
        """
        while True:
            # Generate a random 8-character string of uppercase letters and digits
            reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # Check if this reference is unique
            if reference not in self.booking_references:
                # Add to our set of references to prevent future duplicates
                self.booking_references.add(reference)
                return reference

    def close_database(self):
        """Close the database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


class SeatBookingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seat Booking System")
        self.booking_system = SeatBookingSystem()

        window_width = 1200
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_menu()
        self.create_widgets()
        self.create_seating_display()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        operations_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operations", menu=operations_menu)
        operations_menu.add_command(label="Book Selected Seats", command=lambda: self.book_selected_seats(False))
        operations_menu.add_command(label="Free Selected Seats", command=self.free_selected_seats)
        operations_menu.add_command(label="Check Status", command=self.check_selected_status)
        operations_menu.add_separator()
        operations_menu.add_command(label="Exit", command=self.on_closing)

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_label = ttk.Label(self.main_frame, text="Seat Booking System", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Center menu frame
        center_frame = ttk.Frame(self.main_frame)
        center_frame.grid(row=1, column=0, columnspan=2, pady=5)

        # Menu buttons frame
        menu_frame = ttk.LabelFrame(center_frame, text="Menu", padding="5")
        menu_frame.pack(pady=5)

        button_width = 15
        padding = 3

        ttk.Button(menu_frame, text="Book Seats", width=button_width,
                   command=lambda: self.book_selected_seats(False)).grid(row=0, column=0, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Free Seats", width=button_width,
                   command=self.free_selected_seats).grid(row=0, column=1, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Check Status", width=button_width,
                   command=self.check_selected_status).grid(row=1, column=0, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Exit", width=button_width,
                   command=self.on_closing).grid(row=1, column=1, padx=padding, pady=padding)

        self.status_var = tk.StringVar()
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var, wraplength=600)
        status_label.grid(row=2, column=0, columnspan=2, pady=10)

    def create_seating_display(self):
        canvas_frame = ttk.LabelFrame(self.main_frame, text="Seating Layout", padding="10")
        canvas_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        canvas = tk.Canvas(canvas_frame, width=1150, height=300)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar.set)

        scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.seats_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.seats_frame, anchor="nw")

        ttk.Label(self.seats_frame, text="   ").grid(row=0, column=0)
        for col in range(self.booking_system.num_cols):
            if (col + 1) % 5 == 0:
                ttk.Label(self.seats_frame, text=f"{col + 1}", font=('Helvetica', 8)).grid(row=0, column=col + 1)

        self.seat_buttons = []
        for row in range(self.booking_system.num_rows):
            row_buttons = []
            ttk.Label(self.seats_frame, text=f"{self.booking_system.row_letters[row]}:").grid(row=row + 1, column=0,
                                                                                              padx=2)
            for col in range(self.booking_system.num_cols):
                status, seat_type, _ = self.booking_system.seats[row][col]
                # Use 'R' for display if it's a booking reference
                display_text = status if status in ['F', 'A', 'S'] else 'R'

                seat_button = tk.Label(self.seats_frame, text=display_text,
                                       width=2, relief="raised", borderwidth=1, fg='black')
                seat_button.grid(row=row + 1, column=col + 1, padx=1, pady=1)
                seat_button.bind('<Button-1>', lambda e, r=row, c=col: self.on_seat_click(r, c))

                self.update_seat_color(seat_button, status, seat_type)
                row_buttons.append(seat_button)
            self.seat_buttons.append(row_buttons)

        self.seats_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def update_seat_color(self, button, status, seat_type, is_selected=False):
        base_color = self.booking_system.seat_types.get(seat_type, 'white')

        if is_selected:
            button.configure(bg='yellow', relief="sunken", fg='black')
        else:
            if self.booking_system.is_booking_reference(status):  # Modified to check for booking references
                button.configure(bg='lightgreen', relief="raised", fg='black')
            else:
                if seat_type == 'First':
                    button.configure(bg=base_color, relief="solid", borderwidth=2, highlightbackground='gold',
                                     highlightthickness=2, fg='black')
                else:
                    button.configure(bg=base_color, relief="raised", fg='black')

    def on_seat_click(self, row, col):
        success, message = self.booking_system.toggle_seat_selection(row, col)
        if message is not None:  # Only update if there was a selection change
            self.update_status(message)
            self.update_seat_display()

    def get_passenger_info(self):
        """Get passenger information using a dialog"""
        dialog = PassengerInfoDialog(self.root)
        self.root.wait_window(dialog.top)
        return dialog.result

    def book_selected_seats(self, priority=False):
        if not self.booking_system.selected_seats:
            self.update_status("No seats selected")
            return

        # Get passenger information
        passenger_info = self.get_passenger_info()
        if not passenger_info:
            self.update_status("Booking cancelled")
            return

        success, message = self.booking_system.book_seats(passenger_info, priority)
        self.update_status(message)
        self.update_seat_display()

    def free_selected_seats(self):
        success, message = self.booking_system.free_seats()
        self.update_status(message)
        self.update_seat_display()

    def check_selected_status(self):
        if not self.booking_system.selected_seats:
            self.update_status("Please select a seat first")
            return

        status_messages = []
        for row, col in self.booking_system.selected_seats:
            status_message = self.booking_system.get_seat_status(row, col)
            status_messages.append(status_message)

        self.update_status("\n".join(status_messages))

    def update_seat_display(self):
        for row in range(self.booking_system.num_rows):
            for col in range(self.booking_system.num_cols):
                status, seat_type, _ = self.booking_system.seats[row][col]
                button = self.seat_buttons[row][col]
                is_selected = (row, col) in self.booking_system.selected_seats
                self.update_seat_color(button, status, seat_type, is_selected)

                # Display 'R' for any booking reference
                display_text = status if status in ['F', 'A', 'S'] else 'R'
                button.configure(text=display_text)

    def update_status(self, message):
        self.status_var.set(message)

    def on_closing(self):
        """Handle window close event"""
        # Close database connection before exiting
        self.booking_system.close_database()
        self.root.destroy()


class PassengerInfoDialog:
    """Dialog for collecting passenger information"""

    def __init__(self, parent):
        self.result = None

        self.top = tk.Toplevel(parent)
        self.top.title("Passenger Information")
        self.top.transient(parent)
        self.top.grab_set()

        # Center the dialog
        window_width = 300
        window_height = 200
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Create form fields
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Passport Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.passport_entry = ttk.Entry(frame, width=20)
        self.passport_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.first_name_entry = ttk.Entry(frame, width=20)
        self.first_name_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(frame, text="Last Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.last_name_entry = ttk.Entry(frame, width=20)
        self.last_name_entry.grid(row=2, column=1, pady=5, padx=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        # Set focus
        self.passport_entry.focus_set()

    def ok_clicked(self):
        """Validate and collect the form data"""
        passport = self.passport_entry.get().strip()
        first_name = self.first_name_entry.get().strip()
        last_name = self.last_name_entry.get().strip()

        # Simple validation
        if not passport or not first_name or not last_name:
            messagebox.showerror("Validation Error", "All fields are required")
            return

        self.result = (passport, first_name, last_name)
        self.top.destroy()

    def cancel_clicked(self):
        """Cancel the dialog"""
        self.top.destroy()


def main():
    root = tk.Tk()
    app = SeatBookingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


