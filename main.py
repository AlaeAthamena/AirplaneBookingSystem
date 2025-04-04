
import tkinter as tk
from tkinter import ttk, messagebox
# Class to manage seat booking logic
class SeatBookingSystem:
    def __init__(self):
        self.num_rows = 7  # Total number of rows in the seating layout
        self.num_cols = 80  # Total number of columns (seats per row)

        # Initialize all seats as free ('F')
        self.seats = [['F' for _ in range(self.num_cols)] for _ in range(self.num_rows)]
        self.row_letters = 'ABCDEFG'  # Row labels for display

        # Mark special seats like aisles and storage areas
        self.mark_special_seats()

        # Variable to track the currently selected seat
        self.selected_seat = None

    # Function to mark aisles and storage areas
    def mark_special_seats(self):
        # Mark row D (index 3) as aisle with 'X'
        for col in range(self.num_cols):
            self.seats[3][col] = 'X'  # Row D is index 3 (A=0, B=1, C=2, D=3)

        # Storage columns (subtract 1 from each number since we're using 0-based indexing)
        storage_columns = [13, 14, 15, 28, 29, 30, 43, 44, 45, 58, 59, 60, 73, 74, 75]

        # Mark storage areas with 'S' for all rows except row D (index 3)
        for col in storage_columns:
            for row in range(self.num_rows):
                if row != 3:  # Skip row D (index 3)
                    self.seats[row][col] = 'S'

    # Function to get seat label (e.g., A1, B5)
    def get_seat_name(self, row, col):
        return f"{self.row_letters[row]}{col + 1}"

    # Function to toggle the booking status of a seat
    def toggle_seat(self, row, col):
        if not (0 <= row < self.num_rows and 0 <= col < self.num_cols):
            return False, "Invalid seat position"

        seat_name = self.get_seat_name(row, col)

        if self.seats[row][col] == 'F':
            self.seats[row][col] = 'R'  # Mark seat as reserved
            return True, f"Seat {seat_name} booked successfully"
        elif self.seats[row][col] == 'R':
            self.seats[row][col] = 'F'  # Mark seat as free
            return True, f"Seat {seat_name} freed successfully"
        elif self.seats[row][col] == 'X':
            return False, f"Seat {seat_name} is an aisle"
        elif self.seats[row][col] == 'S':
            return False, f"Seat {seat_name} is a storage area"

        return False, "Invalid seat"

    # Function to get the booking status of a seat
    def get_booking_status(self, row, col):
        if not (0 <= row < self.num_rows and 0 <= col < self.num_cols):
            return "Invalid seat position"

        seat_name = self.get_seat_name(row, col)
        status_map = {
            'F': 'Free',
            'R': 'Reserved',
            'X': 'Aisle',
            'S': 'Storage'
        }
        status = status_map.get(self.seats[row][col], 'Unknown')
        return f"Seat {seat_name} is {status}"

    # Function to handle seat selection logic
    def toggle_selection(self, row, col):
        if self.selected_seat == (row, col):
            # If clicking the same seat, deselect it
            self.selected_seat = None
            return None
        else:
            # Select the new seat
            self.selected_seat = (row, col)
            return self.get_seat_name(row, col)



