import tkinter as tk
from tkinter import messagebox, filedialog
import serial
import threading
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DynamoControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamo Control and Monitoring")
        
        # Set the background color
        self.root.configure(bg='#80ed99')
        
        # Set window size to 100% of the screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        
        self.serial_port = 'COM3'  # Update this to your Arduino's COM port
        self.baud_rate = 9600
        self.arduino = None
        self.connect_serial()

        self.create_widgets()
        
        self.is_recording = False
        self.is_monitoring = False
        self.data = {"Set Point": [], "Output": []}
        self.set_point_data = []
        self.output_data = []
        
        # Start a separate thread for reading RPM from Arduino
        self.reading_thread = threading.Thread(target=self.update_rpm_label)
        self.reading_thread.daemon = True
        self.reading_thread.start()
        
    def connect_serial(self):
        try:
            self.arduino = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to {self.serial_port}\n{e}")
            self.root.quit()

    def create_widgets(self):
        self.rpm_input_label = tk.Label(self.root, text="RPM input keypad: 0", font=("Helvetica", 16), bg='#80ed99')
        self.rpm_input_label.pack(pady=10)
        
        self.set_point_label = tk.Label(self.root, text="Set point: 0", font=("Helvetica", 16), bg='#80ed99')
        self.set_point_label.pack(pady=10)
        
        self.output_label = tk.Label(self.root, text="Output: 0", font=("Helvetica", 16), bg='#80ed99')
        self.output_label.pack(pady=10)
        
        # Create a frame for the graph
        self.graph_frame = tk.Frame(self.root, bg='#80ed99')
        self.graph_frame.pack(pady=10)
        
        # Create the graph
        self.fig, self.ax = plt.subplots()
        self.ax.set_ylim(0, 7000)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack()

        self.rpm_entry_label = tk.Label(self.root, text="Enter RPM:", font=("Helvetica", 12), bg='#80ed99')
        self.rpm_entry_label.pack(pady=5)
        
        self.rpm_entry_frame = tk.Frame(self.root, bg='#80ed99')
        self.rpm_entry_frame.pack(pady=5)

        self.rpm_minus_button = tk.Button(self.rpm_entry_frame, text="-", font=("Helvetica", 12), command=self.decrement_rpm)
        self.rpm_minus_button.pack(side=tk.LEFT)

        self.rpm_entry = tk.Entry(self.rpm_entry_frame, font=("Helvetica", 12), width=10)
        self.rpm_entry.pack(side=tk.LEFT)
        self.rpm_entry.bind("<KeyRelease>", self.update_slider)

        self.rpm_plus_button = tk.Button(self.rpm_entry_frame, text="+", font=("Helvetica", 12), command=self.increment_rpm)
        self.rpm_plus_button.pack(side=tk.LEFT)

        slider_frame = tk.Frame(self.root, bg='#80ed99')
        slider_frame.pack(pady=5)

        self.rpm_slider_min_label = tk.Label(slider_frame, text="Min: 0", font=("Helvetica", 12), bg='#80ed99')
        self.rpm_slider_min_label.pack(side=tk.LEFT, padx=10)

        self.rpm_slider = tk.Scale(slider_frame, from_=0, to=5000, orient=tk.HORIZONTAL, length=400, command=self.update_rpm_entry)
        self.rpm_slider.pack(side=tk.LEFT)

        self.rpm_slider_max_label = tk.Label(slider_frame, text="Max: 5000", font=("Helvetica", 12), bg='#80ed99')
        self.rpm_slider_max_label.pack(side=tk.LEFT, padx=10)
        
        self.set_rpm_button = tk.Button(self.root, text="START", font=("Helvetica", 12), command=self.start_monitoring, bg='#80ed99')
        self.set_rpm_button.pack(pady=10)

        # Create the "Stop" button
        self.stop_button = tk.Button(self.root, text="Stop", font=("Helvetica", 12), command=self.stop_monitoring, bg='#80ed99')
        self.stop_button.pack(pady=10)

        # Create the "Save" button
        self.save_button = tk.Button(self.root, text="Save", font=("Helvetica", 12), command=self.save_recording, bg='#80ed99')
        self.save_button.pack(pady=10)

    def increment_rpm(self):
        current_rpm = int(self.rpm_entry.get())
        new_rpm = min(current_rpm + 5, 5000)
        self.update_rpm_entry(new_rpm)
        self.rpm_slider.set(new_rpm)

    def decrement_rpm(self):
        current_rpm = int(self.rpm_entry.get())
        new_rpm = max(current_rpm - 5, 0)
        self.update_rpm_entry(new_rpm)
        self.rpm_slider.set(new_rpm)

    def update_rpm_entry(self, value):
        self.rpm_entry.delete(0, tk.END)
        self.rpm_entry.insert(0, value)

    def update_slider(self, event):
        rpm_value = self.rpm_entry.get()
        if rpm_value.isdigit():
            self.rpm_slider.set(int(rpm_value))

    def start_monitoring(self):
        rpm = self.rpm_entry.get()
        if rpm.isdigit():
            self.is_monitoring = True
            self.is_recording = True
            self.set_rpm()
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid RPM value.")

    def set_rpm(self):
        if self.arduino:
            rpm = self.rpm_entry.get()
            try:
                self.arduino.write(f'{rpm}#'.encode())
            except serial.SerialException as e:
                messagebox.showerror("Communication Error", f"Failed to write to {self.serial_port}\n{e}")
        else:
            messagebox.showerror("Connection Error", "Arduino is not connected.")
        
    def stop_monitoring(self):
        if self.arduino:
            try:
                self.arduino.write(b'0#')
                self.is_monitoring = False
            except serial.SerialException as e:
                messagebox.showerror("Communication Error", f"Failed to write to {self.serial_port}\n{e}")
        else:
            messagebox.showerror("Connection Error", "Arduino is not connected.")
        
    def save_recording(self):
        self.is_recording = False
        self.save_data_to_excel()
        self.clear_data()
        
    def clear_data(self):
        self.data = {"Set Point": [], "Output": []}
        self.set_point_data = []
        self.output_data = []
        self.ax.clear()
        self.ax.set_ylim(0, 7000)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.canvas.draw()

    def save_data_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if file_path:
            # Make sure both lists in self.data have the same length
            max_len = max(len(self.data["Set Point"]), len(self.data["Output"]))
            self.data["Set Point"].extend([None] * (max_len - len(self.data["Set Point"])))
            self.data["Output"].extend([None] * (max_len - len(self.data["Output"])))

            df = pd.DataFrame(self.data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Save Data", f"Data has been saved to {file_path}")

    def update_rpm_label(self):
        while True:
            if self.arduino:
                try:
                    line = self.arduino.readline().decode('utf-8').strip()
                    if self.is_monitoring:
                        if line.isdigit():
                            self.rpm_input_label.config(text=f"RPM input keypad: {line}")
                        elif line.startswith("Set point:"):
                            set_point = int(line.split(":")[1])
                            self.set_point_label.config(text=f"Set point: {set_point}")
                            self.set_point_data.append(set_point)
                            if self.is_recording:
                                self.data["Set Point"].append(set_point)
                        elif line.startswith("Output:"):
                            arduino_output = int(line.split(":")[1])
                            self.output_label.config(text=f"Output: {arduino_output}")
                            self.output_data.append(arduino_output)
                            if self.is_recording:
                                self.data["Output"].append(arduino_output)
                        
                        # Update the graph
                        self.ax.clear()
                        self.ax.plot(self.set_point_data, label="Set Point", color="blue")
                        self.ax.plot(self.output_data, label="Output", color="red")
                        self.ax.set_ylim(0, 7000)
                        self.ax.set_xlabel("Time")
                        self.ax.set_ylabel("Value")
                        self.ax.legend()
                        self.canvas.draw()
                    else:
                        # Clear the labels when not monitoring
                        self.rpm_input_label.config(text="RPM input keypad: 0")
                        self.set_point_label.config(text="Set point: 0")
                        self.output_label.config(text="Output: 0")
                        
                except serial.SerialException as e:
                    messagebox.showerror("Communication Error", f"Failed to read from {self.serial_port}\n{e}")
                    self.arduino.close()
                    self.arduino = None
                    self.connect_serial()
                except UnicodeDecodeError:
                    # Skip lines that can't be decoded
                    continue
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = DynamoControlApp(root)
    root.mainloop()
