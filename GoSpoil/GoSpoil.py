import tkinter as tk
from PIL import ImageTk, Image

def button_click():
    print("Button clicked!")

image_path = ""
original_image = Image.open(image_path)





root = tk.Tk()
root.title("My Tkinter App")
root.geometry("900x900")
root.configure(bg='lightblue')

label = tk.Label(root, text="Welcome to my app!", font=("Arial", 14))
label.pack(pady=10)

button = tk.Button(root, text="Perform Action", command=button_click)
button.pack(pady=5)

entry = tk.Entry(root, width=30)
entry.pack(pady=5)

root.mainloop()