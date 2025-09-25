
import tkinter as tk
from gui.annotation_tool import AnnotationTool

def main():
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
