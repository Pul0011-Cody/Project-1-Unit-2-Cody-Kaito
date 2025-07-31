import tkinter as tk

def button_click():
    print("Button clicked!")

root = tk.Tk()
root.title("GoSpoil")
root.geometry("600x600")


tk_image = tk.PhotoImage(file="Images/Shrek.gif").subsample(3, 3)

label = tk.Label(root, image=tk_image)
label.image = tk_image  
label.pack(pady=10)

button = tk.Button(root, text="Perform Action", command=button_click)
button.pack(pady=5)

entry = tk.Entry(root, width=30)
entry.pack(pady=5)

root.mainloop()