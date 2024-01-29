import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
import datetime
import logging
import csv

class AttendanceTracker:
    def __init__(self, root):
        # Initialize logging
        logging.basicConfig(filename='attendance_tracker.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        self.root = root
        self.root.title("Attendance Tracker")

        self.schedule = {}
        self.absences = {}
        self.cancelled_classes = {}

        # Connect to the SQLite database
        self.conn = sqlite3.connect('attendance.db')
        self.create_tables()

        self.create_widgets()
        self.load_data()  # Load attendance, absences, and cancelled classes from the database

    def create_background(self):
        background_color = "#E6E6FA"  # Light gray background color
        self.root.configure(bg=background_color)

    def reset_data(self):
        confirm = messagebox.askyesno("Reset Data", "Are you sure you want to reset all data?")
        if confirm:
            self.schedule = {}
            self.absences = {}
            self.cancelled_classes = {}
            self.conn.execute("DELETE FROM schedule")
            self.conn.execute("DELETE FROM attendance")
            self.conn.execute("DELETE FROM absences")
            self.conn.execute("DELETE FROM cancelled_classes")
            self.conn.commit()
            messagebox.showinfo("Reset Data", "All data has been reset.")

    def create_widgets(self):
        self.create_background()

        self.main_frame = tk.Frame(self.root, bg="#7B68EE")
        self.main_frame.pack(padx=20, pady=20)

        title_label = tk.Label(self.main_frame, text="Attendance Tracker", font=("Arial", 24, "bold"), bg="#FFC0CB")
        title_label.pack(pady=20)

        button_frame = tk.Frame(self.main_frame, bg="#6A0DAD")
        button_frame.pack()

        self.generate_template_button = tk.Button(button_frame, text="Generate Schedule Template",
                                                  command=self.generate_schedule_template, font=("Arial", 12, "bold"))
        self.generate_template_button.pack(side="left", padx=10, pady=10)

        self.new_user_button = tk.Button(button_frame, text="New User Registration",
                                         command=self.new_user_registration, font=("Arial", 12, "bold"))
        self.new_user_button.pack(side="left", padx=10, pady=10)

        self.today_classes_button = tk.Button(button_frame, text="Today's Classes",
                                              command=self.show_today_classes, font=("Arial", 12, "bold"))
        self.today_classes_button.pack(side="left", padx=10, pady=10)

        self.absent_classes_button = tk.Button(button_frame, text="Absent Classes",
                                               command=self.mark_absent_classes, font=("Arial", 12, "bold"))
        self.absent_classes_button.pack(side="left", padx=10, pady=10)

        self.cancelled_class_button = tk.Button(button_frame, text="Cancelled Class",
                                                command=self.mark_cancelled_class, font=("Arial", 12, "bold"))
        self.cancelled_class_button.pack(side="left", padx=10, pady=10)

        self.attendance_button = tk.Button(button_frame, text="Attendance",
                                           command=self.calculate_attendance, font=("Arial", 12, "bold"))
        self.attendance_button.pack(side="left", padx=10, pady=10)

        self.reset_button = tk.Button(button_frame, text="Reset Data",
                                      command=self.reset_data, font=("Arial", 12, "bold"))
        self.reset_button.pack(side="left", padx=10, pady=10)

        self.exit_button = tk.Button(button_frame, text="Exit",
                                     command=self.exit_application, font=("Arial", 12, "bold"))
        self.exit_button.pack(side="left", padx=10, pady=10)

    def log_info(self, message):
        logging.info(message)

    def log_error(self, message):
        logging.error(message)

    def new_user_registration(self):
        # Prompt the user to select a class schedule file
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            try:
                # Read the class schedule from the Excel file
                df = pd.read_excel(file_path)
                for _, row in df.iterrows():
                    day = row['Day']
                    class_names = [row[f'Class{i}'] for i in range(1, 7) if not pd.isnull(row[f'Class{i}'])]
                    for class_name in class_names:
                        self.add_class(day, class_name)

                # Save the class schedule data permanently
                df.to_excel("class_schedule_data.xlsx", index=False)
                messagebox.showinfo("New User Registration", "Class schedule registered successfully!")
                self.log_info("New user registration successful.")
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while reading the class schedule: {str(e)}")
                self.log_error(f"Error occurred while reading the class schedule: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No file selected. Registration cancelled.")
            self.log_info("New user registration cancelled: No file selected.")

    def generate_schedule_template(self):
        template_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if template_file:
            try:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                df = pd.DataFrame(columns=["Day"] + [f"Class{i}" for i in range(1, 7)])
                df["Day"] = days
                df.to_excel(template_file, index=False)
                messagebox.showinfo("Schedule Template",
                                    "Schedule template generated successfully!\nPlease fill in the class details in the Excel file.")
                self.log_info("Schedule template generated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while generating schedule template: {str(e)}")
                self.log_error(f"Error occurred while generating schedule template: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No file selected. Template generation cancelled.")
            self.log_info("Template generation cancelled: No file selected.")


    def show_today_classes(self):
        today = datetime.datetime.now().strftime("%A")
        classes = self.schedule.get(today, [])
        try:
            if classes:
                class_list = "\n".join(classes)
                messagebox.showinfo("Today's Classes", f"Classes for {today}:\n\n{class_list}")
                self.log_info(f"Displayed today's classes for {today}.")
            else:
                messagebox.showinfo("Today's Classes", f"No classes scheduled for {today}.")
                self.log_info(f"No classes scheduled for {today}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while displaying today's classes: {str(e)}")
            self.log_error(f"Error occurred while displaying today's classes: {str(e)}")

    def mark_absent_classes(self):
        today = datetime.datetime.now().strftime("%A")
        classes = self.schedule.get(today, [])
        try:
            if classes:
                absent_classes = []
                for class_name in classes:
                    response = messagebox.askyesno("Absent Classes", f"Did you attend the class: {class_name}?")
                    if not response:
                        absent_classes.append(class_name)
                if absent_classes:
                    self.store_absent_classes(absent_classes)
                    messagebox.showinfo("Absent Classes", "Absent classes recorded successfully!")
                    self.log_info("Absent classes recorded successfully.")
                else:
                    messagebox.showinfo("Absent Classes", "No absent classes recorded.")
                    self.log_info("No absent classes recorded.")
            else:
                messagebox.showinfo("Absent Classes", f"No classes scheduled for {today}.")
                self.log_info(f"No classes scheduled for {today}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while marking absent classes: {str(e)}")
            self.log_error(f"Error occurred while marking absent classes: {str(e)}")

    def mark_cancelled_class(self):
        today = datetime.datetime.now().strftime("%A")
        classes = self.schedule.get(today, [])
        try:
            if classes:
                cancelled_classes = []
                for class_name in classes:
                    response = messagebox.askyesno("Cancelled Class", f"Is the class cancelled: {class_name}?")
                    if response:
                        cancelled_classes.append(class_name)
                if cancelled_classes:
                    self.store_cancelled_classes(cancelled_classes)
                    messagebox.showinfo("Cancelled Class", "Cancelled classes recorded successfully!")
                    self.calculate_attendance()  # Recalculate attendance after marking cancelled classes
                    self.log_info("Cancelled classes recorded successfully.")
                else:
                    messagebox.showinfo("Cancelled Class", "No cancelled classes recorded.")
                    self.log_info("No cancelled classes recorded.")
            else:
                messagebox.showinfo("Cancelled Class", f"No classes scheduled for {today}.")
                self.log_info(f"No classes scheduled for {today}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while marking cancelled class: {str(e)}")
            self.log_error(f"Error occurred while marking cancelled class: {str(e)}")

    def calculate_attendance(self):
        attendance_percentage = {}

        try:
            for day, class_names in self.schedule.items():
                for class_name in class_names:
                    total_classes = len(class_names)
                    attended_classes = total_classes - self.absences.get(class_name, 0)

                    # Exclude cancelled classes from attended_classes
                    cancelled_classes = self.cancelled_classes.get(class_name, 0)
                    attended_classes -= cancelled_classes

                    percentage = (attended_classes / total_classes) * 100 if total_classes > 0 else 0

                    attendance_percentage[class_name] = round(percentage, 2)

            attendance_text = "\nAttendance Percentage:\n"
            for class_name, percentage in attendance_percentage.items():
                attendance_text += f"{class_name}: {percentage}%\n"

            messagebox.showinfo("Attendance Percentage", attendance_text)
            self.log_info("Attendance percentage calculated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while calculating attendance: {str(e)}")
            self.log_error(f"Error occurred while calculating attendance: {str(e)}")

    def create_tables(self):
        try:
            # Create the 'schedule' table if it doesn't exist
            self.conn.execute('''CREATE TABLE IF NOT EXISTS schedule
                                   (day TEXT, class_name TEXT)''')

            # Create the 'absences' table if it doesn't exist
            self.conn.execute('''CREATE TABLE IF NOT EXISTS absences
                                   (class_name TEXT, absences INTEGER)''')

            # Create the 'cancelled_classes' table if it doesn't exist
            self.conn.execute('''CREATE TABLE IF NOT EXISTS cancelled_classes
                                   (class_name TEXT, cancelled INTEGER)''')

            self.log_info("Database tables created successfully.")
        except Exception as e:
            self.log_error(f"Error occurred while creating database tables: {str(e)}")

    def load_data(self):
        try:
            # Load schedule from the database
            cursor = self.conn.cursor()
            cursor.execute("SELECT day, class_name FROM schedule")
            rows = cursor.fetchall()
            for row in rows:
                day, class_name = row
                if day in self.schedule:
                    self.schedule[day].append(class_name)
                else:
                    self.schedule[day] = [class_name]

            # Load absences from the database
            cursor.execute("SELECT class_name, absences FROM absences")
            rows = cursor.fetchall()
            for row in rows:
                class_name, absences = row
                self.absences[class_name] = absences

            # Load cancelled classes from the database
            cursor.execute("SELECT class_name, cancelled FROM cancelled_classes")
            rows = cursor.fetchall()
            for row in rows:
                class_name, cancelled = row
                self.cancelled_classes[class_name] = cancelled

            self.log_info("Data loaded successfully.")
        except Exception as e:
            self.log_error(f"Error occurred while loading data: {str(e)}")

    def add_class(self, day, class_name):
        try:
            if day in self.schedule:
                self.schedule[day].append(class_name)
            else:
                self.schedule[day] = [class_name]
            self.absences[class_name] = 0

            # Insert the class into the 'schedule' table
            self.conn.execute("INSERT INTO schedule (day, class_name) VALUES (?, ?)", (day, class_name))
            self.conn.commit()

            self.log_info(f"Class added successfully: {class_name} on {day}.")
        except Exception as e:
            self.log_error(f"Error occurred while adding class: {str(e)}")

    def store_absent_classes(self, absent_classes):
        today = datetime.datetime.now().strftime("%A")
        try:
            for class_name in absent_classes:
                if class_name in self.absences:
                    self.absences[class_name] += 1
                else:
                    self.absences[class_name] = 1
                # Update the absences in the 'absences' table
                self.conn.execute("INSERT INTO absences (class_name, absences) VALUES (?, ?)",
                                  (class_name, self.absences[class_name]))
            self.conn.commit()
            self.log_info("Absent classes recorded successfully.")
        except Exception as e:
            self.log_error(f"Error occurred while storing absent classes: {str(e)}")

    def store_cancelled_classes(self, cancelled_classes):
        today = datetime.datetime.now().strftime("%A")
        try:
            for class_name in cancelled_classes:
                if class_name in self.cancelled_classes:
                    self.cancelled_classes[class_name] += 1
                else:
                    self.cancelled_classes[class_name] = 1
                # Update the cancelled classes in the 'cancelled_classes' table
                self.conn.execute("INSERT INTO cancelled_classes (class_name, cancelled) VALUES (?, ?)",
                                  (class_name, self.cancelled_classes[class_name]))
            self.conn.commit()
            self.log_info("Cancelled classes recorded successfully.")
        except Exception as e:
            self.log_error(f"Error occurred while storing cancelled classes: {str(e)}")

    def generate_updated_attendance_csv(self, output_file="updated_attendance.csv"):
        try:
            with open(output_file, mode='w', newline='') as csv_file:
                fieldnames = ['Day', 'Class', 'Attendance Percentage']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                writer.writeheader()

                for day, class_names in self.schedule.items():
                    for class_name in class_names:
                        total_classes = len(class_names)
                        attended_classes = total_classes - self.absences.get(class_name, 0)
                        cancelled_classes = self.cancelled_classes.get(class_name, 0)

                        # Exclude cancelled classes from attended_classes
                        attended_classes -= cancelled_classes

                        percentage = (attended_classes / total_classes) * 100 if total_classes > 0 else 0

                        writer.writerow({
                            'Day': day,
                            'Class': class_name,
                            'Attendance Percentage': round(percentage, 2)
                        })

            messagebox.showinfo("Updated Attendance CSV", f"Updated attendance data saved to {output_file}.")
            self.log_info(f"Updated attendance data saved to {output_file}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while generating updated attendance CSV: {str(e)}")
            self.log_error(f"Error occurred while generating updated attendance CSV: {str(e)}")

    def exit_application(self):
        try:
            confirm = messagebox.askyesno("Exit", "Are you sure you want to exit the application?")
            if confirm:
                self.root.destroy()
                self.log_info("Application exited.")
        except Exception as e:
            self.log_error(f"Error occurred while exiting application: {str(e)}")


def main():
    try:
        root = tk.Tk()
        app = AttendanceTracker(root)
        root.mainloop()
    except Exception as e:
        log_error(f"Error occurred in main: {str(e)}")

if __name__ == "__main__":
    main()


