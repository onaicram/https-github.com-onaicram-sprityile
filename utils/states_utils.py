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

    print(f"[SAVE] undo_stack: {len(undo_stack)}, redo_stack: {len(redo_stack)}")
    print(f"       selection: {state['selection']}")


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
    print(f"[UNDO] BEFORE → undo_stack: {len(undo_stack)}, redo_stack: {len(redo_stack)}")
    if len(undo_stack) <= 1:
        print("[UNDO] Stack troppo corto, impossibile annullare.")
        return
    current = undo_stack.pop()
    redo_stack.append(current)
    previous = undo_stack[-1]

    print(f"[UNDO] AFTER → undo_stack: {len(undo_stack)}, redo_stack: {len(redo_stack)}")
    print(f"        selection: {previous['selection']}")

    apply_state(pixmap_item, selected_coords, previous, restore_selection_fn)


def redo_state(pixmap_item, selected_coords: set, undo_stack: list, redo_stack: list, restore_selection_fn=None):
    print(f"[REDO] BEFORE → undo_stack: {len(undo_stack)}, redo_stack: {len(redo_stack)}")

    if not redo_stack:
        print("[REDO] Stack vuoto, niente da rifare.")
        return
    
    next_state = redo_stack.pop()
    undo_stack.append(next_state)

    print(f"[REDO] AFTER → undo_stack: {len(undo_stack)}, redo_stack: {len(redo_stack)}")
    print(f"        selection: {next_state['selection']}")

    apply_state(pixmap_item, selected_coords, next_state, restore_selection_fn)


def reset_state(pixmap_item, original_pixmap: QPixmap, selected_coords: set,
                undo_stack: list, redo_stack: list, restore_selection_fn=None, color_field=None, parent=None):
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

    if parent:
        QMessageBox.information(parent, "Reset", "Immagine ripristinata.")

    print(f"[RESET] Reset completo. Undo stack len: {len(undo_stack)}")

