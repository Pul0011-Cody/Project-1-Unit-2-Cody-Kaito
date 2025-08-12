import tkinter as tk
import time

# Track drag vs click
drag_start_x = None
dragging = False

def create_scrollable_image_row(parent, image_paths, image_scale=2):
    canvas = tk.Canvas(parent, height=160)
    canvas.pack(fill="x", padx=10, pady=5)

    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    images = []
    for i, path in enumerate(image_paths):
        img = tk.PhotoImage(file=path).subsample(image_scale, image_scale)
        images.append(img)

        btn = tk.Label(frame, image=img, borderwidth=0)
        btn.image = img
        btn.pack(side="left", padx=5)

        # Bind mouse events for drag + click
        btn.bind("<Button-1>", lambda e, i=i, p=path: start_drag(e, canvas))
        btn.bind("<B1-Motion>", lambda e, c=canvas: do_drag(e, c))
        btn.bind("<ButtonRelease-1>", lambda e, i=i, p=path: end_drag(e, i, p))

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    frame.bind("<Configure>", on_configure)
    return frame, canvas

def start_drag(event, canvas):
    global drag_start_x, dragging
    drag_start_x = event.x_root
    dragging = False
    canvas.scan_mark(event.x, event.y)

def do_drag(event, canvas):
    global dragging
    dragging = True
    canvas.scan_dragto(event.x, event.y, gain=1)

def end_drag(event, index, path):
    global dragging
    if not dragging:
        on_image_click(index, path)

def on_image_click(index, path):
    for widget in root.winfo_children():
        widget.pack_forget()

    enlarged_img = tk.PhotoImage(file=path)
    enlarged_label = tk.Label(root, image=enlarged_img)
    enlarged_label.image = enlarged_img
    enlarged_label.pack(pady=20)

    back_btn = tk.Button(root, text="Back", command=restore_main_screen)
    back_btn.pack(pady=10)

def restore_main_screen():
    for widget in root.winfo_children():
        widget.pack_forget()
    build_main_screen()

def build_main_screen():
    create_scrollable_image_row(root, image_paths)
    create_scrollable_image_row(root, image_paths2)

root = tk.Tk()
root.title("GoSpoil")
root.geometry("600x600")

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

build_main_screen()
root.mainloop()