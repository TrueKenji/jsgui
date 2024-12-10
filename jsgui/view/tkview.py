import numpy as np
import tkinter as tk
try:
    import tkinterdnd2
except:
    tkinterdnd2 = None
from tkinter import filedialog, messagebox
from idlelib.tooltip import Hovertip
from copy import deepcopy
from typing import Union, TypedDict, Optional, List
from .view import View
from decomply import Decomply
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..jsgui import Controller
    from ..json_schema_model import JSONSchemaModel


class Node(TypedDict):
    """type class reflecting the specification of a concreted property in the given json schema
    example:
    schema = {
      properties: {
        name: {
          value: MaxMuster
          type: string,
          enum: [MaxMuster, MariaMuster]
        }
      }
    }
    the node specifying 'name' would be
    node = {
      value: MaxMuster
      type: string,
      enum: [MaxMuster, MariaMuster]
    }
    """
    value: Optional[Union[str, int]]
    enum: Optional[List[Union[str, int]]]


class DelayableEntry(tk.Entry):
    """tk entry widget which allows to include a delay before executing a callback
    """

    def __init__(self, master=None, callback=None, delay=0, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.callback = callback
        self.delay = delay
        self.after_id = None
        self.bind("<KeyRelease>", self.on_key_release)

    def on_key_release(self, event: tk.Event) -> None:
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.after_id = self.after(
            self.delay, lambda: self.callback_wrapper(event))

    def callback_wrapper(self, event: tk.Event) -> None:
        if self.callback:
            self.callback(event)


class TKView(View):

    def __init__(self, controller: 'Controller') -> None:
        """Build the basic frame
        Layout is as follows:
        tkinterdnd2 as root to enable drag and drop functionality
        Canvas on top to enable Scrollbars
        Frame inside the Canvas, also to enable Scrollbars
        Menu bar topside (load and save buttons)
        Populating the frame with widgets happens in @paint
        """
        super().__init__(controller)

        if tkinterdnd2:
            self.root = tkinterdnd2.Tk()
            self.root.drop_target_register(tkinterdnd2.DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.drop)
        else:
            self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.title("JSON Schema-based Editor")

        # create a scrollable canvas with a main window inside
        self.canvas = tk.Canvas(self.root)

        hbar = tk.Scrollbar(self.root, orient="horizontal")
        hbar.pack(side="bottom", fill="x")
        hbar.config(command=self.canvas.xview)
        vbar = tk.Scrollbar(self.root, orient="vertical")
        vbar.pack(side="right", fill="y")
        vbar.config(command=self.canvas.yview)

        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side="left", expand=True, fill="both")

        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        # Bind the mouse wheel event to the canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        # For Linux systems
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

        self.add_control_buttons()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.7)
        height = int(screen_height * 0.7)
        self.root.geometry(f"{width}x{height}")

    def drop(self, event: tk.Event) -> None:
        file_path = event.data
        self.load(file_path)

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        if event.num == 4:  # For Linux systems
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # For Linux systems
            self.canvas.yview_scroll(1, "units")
        else:  # For Windows and MacOS
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_control_buttons(self) -> None:
        menubar = tk.Menu(self.root)

        load_menu = tk.Menu(menubar, tearoff=0)
        load_menu.add_command(label="Load Schema",
                              command=lambda: self.load_command(True))
        load_menu.add_command(
            label="Load JSON", command=lambda: self.load_command(False))
        menubar.add_cascade(label="Load", menu=load_menu)

        save_menu = tk.Menu(menubar, tearoff=0)
        save_menu.add_command(label="Save", command=self.controller.save)
        menubar.add_cascade(label="Save", menu=save_menu)

        self.root.config(menu=menubar)

    def mainloop(self) -> None:
        self.root.mainloop()

    def popup_showerror(self, title: str, msg: str) -> None:
        messagebox.showerror(title, msg)

    def load(self, file_path: str, schema_flg: bool = None) -> None:
        self.controller.load(file_path, schema_flg)
        self.canvas.pack()

    def load_command(self, schema_flg: bool) -> None:
        folder_selected = filedialog.askopenfile()
        if hasattr(folder_selected, "name"):
            self.load(folder_selected.name, schema_flg)

    def save(self) -> str:
        return filedialog.asksaveasfile(mode="w", defaultextension=".json")

    def _create_widget(self, item: Node, trace: List[Union[str, int]], row: int, col: int) -> None:
        """create a concrete, user editable widget like textfield or dropdown

        Args:
            item (Node): containing the specification of the widget according to the schema
            trace (List[Union[str, int]]): a list of keys
            row (int): position in the grid
            col (int): position in the grid
        """
        value = item["value"] if "value" in item else None
        if "enum" in item:
            string_var = tk.StringVar(
                value=value if value else item["enum"][0])
            widget = tk.OptionMenu(self.frame, string_var, *item["enum"])
        else:
            string_var = tk.StringVar(value=value)
            widget = tk.Entry(self.frame, textvariable=string_var)

        string_var.trace_add("write", lambda a, b, c: self.controller.widget_value_changed(
            trace, string_var.get()))
        widget.grid(row=row, column=col, sticky="w")

    def paint(self, model: "JSONSchemaModel") -> None:
        """Paint the canvas. Destroy all widgets and rebuild.
        The widgets are built by looping through the entire model. At each second layer, a checkbox per currently available
        key is created. If active, the next layers of that key must be looped through as well. We must always go in double
        steps, because the schema works in double layers per key.

        Args:
            model (JSONSchemaModel): the model to paint
        """
        for widget in self.frame.winfo_children():
            widget.destroy()

        value_holders = []  # to prevent the garbage collector?

        traverse_keywords = ["type", "oneOf", "$ref"]
        recursive_keywords = ["oneOf", "properties", "additionalProperties"]

        def traverse(_, item): return np.all(
            [keyword not in item for keyword in traverse_keywords])

        def apply(trace: list, item: dict) -> None:
            """paint the current item and, possibly, start a new decomply, if item["type"] == object

            Args:
                trace (list): a list of keys
                item (dict): the item specification asccociated with the given trace
            """
            if not isinstance(item, dict) and len(trace) < 2:
                return  # skip first layer keys of schema

            # generate Checkbox
            value_holders.append(tk.IntVar())

            def is_disabled():
                required = model.is_required(trace)
                wildcard = (
                    trace[-2] == "additionalProperties") and ("active" not in item or not item["active"])
                return required or wildcard

            state = "disabled" if is_disabled() else "normal"
            checkbox = tk.Checkbutton(
                self.frame,
                text="",
                variable=value_holders[-1],
                command=lambda ids=deepcopy(
                    trace): self.controller.check(ids),
                state=state
            )

            # row is incremented by 1 automatically. col must be 3-step (checkbox+key+value)
            checkbox.grid(column=(int)(len(trace)/2-1)*3, sticky="w")

            # generate key/description field. Possibly editable
            keyField = tk.StringVar()
            callback = None if not trace[-2] == "additionalProperties" else\
                lambda _: self.controller.key_field_changed(
                    trace, keyField.get())
            state = "disabled" if not trace[-2] == "additionalProperties" else "normal"
            delay = 0 if not trace[-2] == "additionalProperties" else 1000
            keyWidget = DelayableEntry(
                self.frame,
                callback=callback,
                delay=delay,
                textvariable=keyField,
                state=state
            )

            keyField.set(trace[-1])
            keyWidget.grid(
                row=checkbox.grid_info()["row"],
                column=checkbox.grid_info()["column"] + 1,
                sticky="w",
            )
            # add the tool tip
            if "$comment" in item:
                checkbox.config(text="*")
                Hovertip(keyWidget, item["$comment"], hover_delay=0)
                Hovertip(checkbox, item["$comment"])

            # paint the subcomponents if checkbox is active
            # append concrete widget or decomply the object
            if "active" in item and item["active"]:
                checkbox.select()
                _trace = deepcopy(trace)
                for recursive_keyword in recursive_keywords:
                    if recursive_keyword in item:
                        _trace.append(recursive_keyword)
                        decomply.decomply(
                            item[recursive_keyword], trace=_trace, initial_check=False
                        )
                        _trace.pop()
                if not np.any([recursive_keyword in item for recursive_keyword in recursive_keywords]):
                    # must be simple/primitive value
                    row = checkbox.grid_info()["row"]
                    col = checkbox.grid_info()["column"] + 2
                    self._create_widget(
                        item=item, trace=trace, row=row, col=col)

        decomply = Decomply(traverse=traverse, apply=apply)
        decomply.decomply(model.schema, initial_check=False)
