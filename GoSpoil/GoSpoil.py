import tkinter as tk

def create_scrollable_image_row(parent, image_paths, image_scale=2):
    # --- Canvas ---
    canvas = tk.Canvas(parent, height=160)
    canvas.pack(fill="x", padx=10, pady=5)

    # --- Scrollbar ---
    scrollbar = tk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
    scrollbar.pack(fill="x")
    canvas.configure(xscrollcommand=scrollbar.set)

    # --- Inner Frame ---
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # --- Load Images ---
    images = []
    for path in image_paths:
        img = tk.PhotoImage(file=path).subsample(image_scale, image_scale)
        images.append(img)  # store reference
        label = tk.Label(frame, image=img)
        label.image = img  # prevent garbage collection
        label.pack(side="left", padx=5)

    # --- Update Scrollregion ---
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    frame.bind("<Configure>", on_configure)
    return frame

# --- Main Window ---
root = tk.Tk()
root.title("GoSpoil")
root.geometry("400x400")

# --- image paths ---
image_paths = [
    "Images/Shrek.gif",
    "Images/Shrek2.gif",
    "Images/Shrek3.gif",
    "Images/Shrekfea.gif",
    "Images/Pussinboots.gif",
    "Images/Pussinbootstlw.gif"
]

image_paths2 = [
    "Images/Theacolyte.gif",
    "Images/Starwarstpm.gif",
    "Images/Starwarsaotc.gif",
    "Images/Starwarstcw.gif",
    "Images/Starwarstcw2.gif",
    "Images/Starwarstotj.gif",
    "Images/Starwarsrots.gif",
    "Images/Starwarstote.gif",
    "Images/Starwarstofu.gif",
    "Images/Starwarstbb.gif",
    "Images/Soloasws.gif",
    "Images/obiwankenobi.gif",
    "Images/Andor.gif",
    "Images/Starwarsrebels.gif",
    "Images/Rogueoneasws.gif",
    "Images/Starwarsanh.gif",
    "Images/Starwarstesb.gif",
    "Images/Starwarsrotj.gif",
    "Images/Themandalorian.gif",
    "Images/Thebookofbobafett.gif",
    "Images/Ahsoka.gif",
    "Images/Skeletoncrew.gif",
    "Images/Starwarsresistance.gif",
    "Images/Starwarstfa.gif",
    "Images/Starwarstlj.gif",
    "Images/Starwarstros.gif"
]

# --- Scrollable Rows ---
create_scrollable_image_row(root, image_paths)
create_scrollable_image_row(root, image_paths2)

root.mainloop()