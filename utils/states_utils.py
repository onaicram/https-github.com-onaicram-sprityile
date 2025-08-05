from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox

def save_state(pixmap_item, selected_coords: set, undo_stack: list, redo_stack: list):
    if not pixmap_item:
        print("save_state: pixmap_item is None")
        return

    state = {
        "pixmap": pixmap_item.pixmap().copy(),
        "selection": set(selected_coords) if selected_coords else set()
    }
    undo_stack.append(state)
    redo_stack.clear()

    # Debug Log
    print(f"[SAVE] Stato salvato. UNDO: {len(undo_stack)} | REDO: {len(redo_stack)} | SEL: {len(selected_coords)}")
    print(f"[SAVE] Selezione: {state['selection']}")

    for i, state in enumerate(undo_stack):
        print(f"---[SAVE] Undo Stack {i}: {state['pixmap']}")

def apply_state(pixmap_item, selected_coords: set, state: dict, restore_selection_fn=None):
    if not state or not pixmap_item:
        return

    if "pixmap" in state:
        pixmap_item.setPixmap(state["pixmap"])

    if "selection" in state and restore_selection_fn:
        restore_selection_fn(state["selection"])

    selected_coords.clear()
    selected_coords.update(state.get("selection", []))

   
def undo_state(pixmap_item, selected_coords: set, undo_stack: list, redo_stack: list, restore_selection_fn=None):
    if len(undo_stack) <= 1:
        print("[UNDO] Stack troppo corto, impossibile annullare.")
        return

    current = undo_stack.pop()
    redo_stack.append(current)
    previous = undo_stack[-1]

    apply_state(pixmap_item, selected_coords, previous, restore_selection_fn)

    # Debug Log
    print(f"[UNDO] UNDO: {len(undo_stack)} | REDO: {len(redo_stack)} | SEL: {previous['selection']}")
    print(f"[UNDO] Pixmap Item: {previous['pixmap']}")
    print(f"[UNDO] TILES: {selected_coords}")

    # stampa il contenuto di undo stack
    for i, state in enumerate(undo_stack):  
        print(f"---[UNDO] Undo Stack {i}: {state['selection']}")

    # stampa il contenuto di redo stack
    for i, state in enumerate(redo_stack):
        print(f"---[UNDO] Redo Stack {i}: {state['selection']}")
    

def redo_state(pixmap_item, selected_coords: set, undo_stack: list, redo_stack: list, restore_selection_fn=None):
    if not redo_stack:
        print("[REDO] Stack vuoto, niente da rifare.")
        return

    next_state = redo_stack.pop()
    undo_stack.append(next_state)

    apply_state(pixmap_item, selected_coords, next_state, restore_selection_fn)

    # Debug Log
    print(f"[REDO] OK → UNDO: {len(undo_stack)} | REDO: {len(redo_stack)} | SEL: {next_state['selection']}")
    print(f"[REDO] Pixmap Item: {next_state['selection']}")
    print(f"[REDO] TILES: {selected_coords}")

    # stampa il contenuto di redo stack
    for i, state in enumerate(redo_stack):
        print(f"---[REDO] Redo Stack {i}: {state['selection']}")

    # stampa il contenuto di undo stack
    for i, state in enumerate(undo_stack):
        print(f"---[REDO] Undo Stack {i}: {state['selection']}")


def reset_state(pixmap_item, original_pixmap: QPixmap, selected_coords: set,
                undo_stack: list, redo_stack: list, restore_selection_fn=None, 
                color_field=None, color_preview=None, current_color=None, parent=None):
    if not pixmap_item or not original_pixmap:
        return

    # Reset immagine
    pixmap_item.setPixmap(QPixmap(original_pixmap))

    # Reset selezione visiva + logica
    if restore_selection_fn and callable(restore_selection_fn):
        restore_selection_fn(set())

    # Reset logico dei dati
    selected_coords.clear()

    # Pulisce gli stack
    undo_stack.clear()
    redo_stack.clear()

    # Stato base iniziale
    state = {
        "pixmap": QPixmap(original_pixmap),
        "selection": set()
    }
    undo_stack.append(state)

    if color_field:
        color_field.setText("Nessun colore")

    if color_preview:
        color_preview.setStyleSheet("background-color: black; border: 1px solid black;")

    if current_color:
        current_color.setRgb(0, 0, 0)

    if parent:
        QMessageBox.information(parent, "Reset", "Immagine ripristinata.")


