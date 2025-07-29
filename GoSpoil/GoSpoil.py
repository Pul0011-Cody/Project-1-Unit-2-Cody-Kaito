import os
import tkinter as tk

def button_click():
    print("Button clicked!")

root = tk.Tk()
root.title("GoSpoil")
root.geometry("600x600")

# Get the folder where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the image relative to the script folder
image_path = os.path.join(script_dir, "Images", "Shrek.gif")

# Load and resize the image
tk_image = tk.PhotoImage(file=image_path).subsample(3, 3)

label = tk.Label(root, image=tk_image)
label.image = tk_image  # prevent garbage collection
label.pack(pady=10)

button = tk.Button(root, text="Shrek", command=button_click)
button.pack(pady=5)

entry = tk.Entry(root, width=30)
entry.pack(pady=5)

root.mainloop()