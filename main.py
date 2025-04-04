import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------- Seat Booking System Logic ----------------------------- #
class SeatBookingSystem:
    def __init__(self):
        self.num_rows = 7
        self.num_cols = 80

        # Initialize all seats as Free ('F') and of Economy type by default
        self.seats = [[('F', 'Economy') for _ in range(self.num_cols)] for _ in range(self.num_rows)]
        self.row_letters = 'ABCDEFG'  # Mapping rows to letters (A to G)
        self.mark_special_seats()     # Mark aisles, storage, and first-class seats
        self.selected_seats = set()   # Track currently selected seats for multi-seat actions

        # Mapping of seat types to their base color in the GUI
        self.seat_types = {
            'Economy': 'white',
            'First': 'white',       # Will distinguish with borders
            'Storage': 'lightgray',
            'Aisle': 'gray'
        }

    def mark_special_seats(self):
        """Marks Aisle, Storage, and First-class seats in the seating arrangement."""

        # Mark the 4th row (index 3) as Aisle across all columns
        for col in range(self.num_cols):
            self.seats[3][col] = ('A', 'Aisle')

        # Predefined columns that represent storage compartments
        storage_columns = [13, 14, 15, 28, 29, 30, 43, 44, 45, 58, 59, 60, 73, 74, 75]
        for col in storage_columns:
            for row in range(self.num_rows):
                if row != 3:  # Don't overwrite the aisle
                    self.seats[row][col] = ('S', 'Storage')

        # First-class section is within the first 30 columns
        for col in range(30):
            for row in range(self.num_rows):
                if self.seats[row][col][0] == 'F':
                    self.seats[row][col] = ('F', 'First')

    def get_seat_name(self, row, col):
        """Returns a human-readable seat name like A1, B23, etc."""
        return f"{self.row_letters[row]}{col + 1}"

    def toggle_seat_selection(self, row, col):
        """Selects or unselects a seat. Only Free or Reserved seats can be selected."""
        seat_pos = (row, col)
        status, seat_type = self.seats[row][col]

        if status not in ['F', 'R']:
            return False, None  # Can't select aisles or storage areas

        # Toggle selection
        if seat_pos in self.selected_seats:
            self.selected_seats.remove(seat_pos)
            return True, f"Unselected seat {self.get_seat_name(row, col)}"
        else:
            self.selected_seats.add(seat_pos)
            return True, f"Selected seat {self.get_seat_name(row, col)}"

    def book_seats(self, priority_booking=False):
        """Books all selected seats if they are free."""
        if not self.selected_seats:
            return False, "No seats selected"

        booked_seats = []
        for row, col in self.selected_seats:
            status, seat_type = self.seats[row][col]
            if status == 'F':
                self.seats[row][col] = ('R', seat_type)  # Change status to Reserved
                booked_seats.append(self.get_seat_name(row, col))

        self.selected_seats.clear()
        return True, f"Booked seats: {', '.join(booked_seats)}"

    def free_seats(self):
        """Frees all selected seats if they are reserved."""
        if not self.selected_seats:
            return False, "No seats selected"

        freed_seats = []
        for row, col in self.selected_seats:
            status, seat_type = self.seats[row][col]
            if status == 'R':
                self.seats[row][col] = ('F', seat_type)  # Change status back to Free
                freed_seats.append(self.get_seat_name(row, col))

        self.selected_seats.clear()
        return True, f"Freed seats: {', '.join(freed_seats)}"

    def get_seat_status(self, row, col):
        """Returns a readable status string for a given seat."""
        if not (0 <= row < self.num_rows and 0 <= col < self.num_cols):
            return "Invalid seat position"

        status, seat_type = self.seats[row][col]
        seat_name = self.get_seat_name(row, col)

        status_map = {
            'F': 'Free',
            'R': 'Reserved',
            'A': 'Aisle',
            'S': 'Storage'
        }

        return f"Seat {seat_name} is {status_map.get(status, 'Unknown')} ({seat_type} Class)"


# ----------------------------- Seat Booking GUI ----------------------------- #
class SeatBookingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seat Booking System")
        self.booking_system = SeatBookingSystem()

        # Centering the window on screen
        window_width = 1200
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # GUI setup
        self.create_menu()
        self.create_widgets()
        self.create_seating_display()

    def create_menu(self):
        """Creates the top-level menu bar with operations."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        operations_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operations", menu=operations_menu)

        operations_menu.add_command(label="Book Selected Seats", command=lambda: self.book_selected_seats(False))
        operations_menu.add_command(label="Free Selected Seats", command=self.free_selected_seats)
        operations_menu.add_command(label="Check Status", command=self.check_selected_status)
        operations_menu.add_separator()
        operations_menu.add_command(label="Exit", command=self.root.quit)

    def create_widgets(self):
        """Creates title and buttons in the main UI."""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_label = ttk.Label(self.main_frame, text="Seat Booking System", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Frame to hold the menu buttons
        center_frame = ttk.Frame(self.main_frame)
        center_frame.grid(row=1, column=0, columnspan=2, pady=5)

        menu_frame = ttk.LabelFrame(center_frame, text="Menu", padding="5")
        menu_frame.pack(pady=5)

        # Create menu buttons
        button_width = 15
        padding = 3
        ttk.Button(menu_frame, text="Book Seats", width=button_width,
                   command=lambda: self.book_selected_seats(False)).grid(row=0, column=0, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Free Seats", width=button_width,
                   command=self.free_selected_seats).grid(row=0, column=1, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Check Status", width=button_width,
                   command=self.check_selected_status).grid(row=1, column=0, padx=padding, pady=padding)
        ttk.Button(menu_frame, text="Exit", width=button_width,
                   command=self.root.quit).grid(row=1, column=1, padx=padding, pady=padding)

        # Label for displaying status messages
        self.status_var = tk.StringVar()
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var, wraplength=600)
        status_label.grid(row=2, column=0, columnspan=2, pady=10)

    def create_seating_display(self):
        """Creates the seating layout with scrollable canvas and clickable seat buttons."""
        canvas_frame = ttk.LabelFrame(self.main_frame, text="Seating Layout", padding="10")
        canvas_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        canvas = tk.Canvas(canvas_frame, width=1150, height=300)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar.set)

        scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.seats_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.seats_frame, anchor="nw")

        # Add column numbers
        ttk.Label(self.seats_frame, text="   ").grid(row=0, column=0)
        for col in range(self.booking_system.num_cols):
            if (col + 1) % 5 == 0:
                ttk.Label(self.seats_frame, text=f"{col + 1}", font=('Helvetica', 8)).grid(row=0, column=col + 1)

        # Create and display seat buttons
        self.seat_buttons = []
        for row in range(self.booking_system.num_rows):
            row_buttons = []
            ttk.Label(self.seats_frame, text=f"{self.booking_system.row_letters[row]}:").grid(row=row + 1, column=0, padx=2)

            for col in range(self.booking_system.num_cols):
                status, seat_type = self.booking_system.seats[row][col]
                seat_button = tk.Label(self.seats_frame, text=status,
                                       width=2, relief="raised", borderwidth=1, fg='black')
                seat_button.grid(row=row + 1, column=col + 1, padx=1, pady=1)
                seat_button.bind('<Button-1>', lambda e, r=row, c=col: self.on_seat_click(r, c))
                self.update_seat_color(seat_button, status, seat_type)
                row_buttons.append(seat_button)
            self.seat_buttons.append(row_buttons)

        self.seats_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def update_seat_color(self, button, status, seat_type, is_selected=False):
        """Updates the visual color/style of a seat button based on its status and selection."""
        base_color = self.booking_system.seat_types.get(seat_type, 'white')

        if is_selected:
            button.configure(bg='yellow', relief="sunken", fg='black')
        else:
            if status == 'R':
                button.configure(bg='lightgreen', relief="raised", fg='black')
            else:
                if seat_type == 'First':
                    button.configure(bg=base_color, relief="solid", borderwidth=2,
                                     highlightbackground='gold', highlightthickness=2, fg='black')
                else:
                    button.configure(bg=base_color, relief="raised", fg='black')

    def on_seat_click(self, row, col):
        """Handles logic when a seat is clicked (select/unselect)."""
        success, message = self.booking_system.toggle_seat_selection(row, col)
        if message is not None:
            self.update_status(message)
            self.update_seat_display()

    def book_selected_seats(self, priority=False):
        """Trigger booking of selected seats."""
        success, message = self.booking_system.book_seats(priority)
        self.update_status(message)
        self.update_seat_display()

    def free_selected_seats(self):
        """Trigger freeing of selected seats."""
        success, message = self.booking_system.free_seats()
        self.update_status(message)
        self.update_seat_display()

    def check_selected_status(self):
        """Display current status for all selected seats."""
        if not self.booking_system.selected_seats:
            self.update_status("Please select a seat first")
            return

        status_messages = []
        for row, col in self.booking_system.selected_seats:
            status_messages.append(self.booking_system.get_seat_status(row, col))

        self.update_status("\n".join(status_messages))

    def update_seat_display(self):
        """Refresh the GUI seat display after updates."""
        for row in range(self.booking_system.num_rows):
            for col in range(self.booking_system.num_cols):
                status, seat_type = self.booking_system.seats[row][col]
                button = self.seat_buttons[row][col]
                is_selected = (row, col) in self.booking_system.selected_seats
                self.update_seat_color(button, status, seat_type, is_selected)
                button.configure(text=status)

    def update_status(self, message):
        """Display a message in the status area of the UI."""
        self.status_var.set(message)


# ----------------------------- Main Entry Point ----------------------------- #
def main():
    root = tk.Tk()
    app = SeatBookingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


