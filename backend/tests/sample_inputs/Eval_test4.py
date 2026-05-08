# inventory.py
# made this for our dbms lab project, tracking items in college store
# gonna add db later, using dict for now
# - Yash, 3rd year CE

import datetime

# using this as global store for now, will move to db later
items = {}
sales_log = []

# forgot what this threshold was supposed to be, keeping 10 for now
LOW_STOCK = 10


def add_item(item_id, name, qty, price):
    # no validation rn, will add later if time permits
    if item_id in items:
        print("item already there bro:", item_id)
        return
    items[item_id] = {
        "name": name,
        "qty": qty,
        "price": price,
        "added": str(datetime.date.today())
    }
    print("added", name)


def restock(item_id, more_qty):
    if item_id not in items:
        print("not found")
        return
    items[item_id]["qty"] += more_qty
    print(f"restocked {items[item_id]['name']} +{more_qty}, now {items[item_id]['qty']}")


def sell_item(item_id, qty_sold):
    if item_id not in items:
        print("item not found:", item_id)
        return False

    item = items[item_id]
    if item["qty"] < qty_sold:
        print(f"not enough stock, only {item['qty']} left")
        return False

    item["qty"] -= qty_sold
    total = qty_sold * item["price"]

    sales_log.append({
        "item_id": item_id,
        "name": item["name"],
        "qty": qty_sold,
        "total": total,
        "date": str(datetime.date.today())
    })

    print(f"sold {qty_sold}x {item['name']} for Rs.{total}")

    if item["qty"] < LOW_STOCK:
        print(f"  [warning] {item['name']} low stock: {item['qty']} remaining")

    return True


def show_inventory():
    if not items:
        print("nothing in inventory")
        return
    print("\ncurrent stock:")
    for iid, data in items.items():
        flag = " <-- LOW" if data["qty"] < LOW_STOCK else ""
        print(f"  {iid} | {data['name']:<20} qty={data['qty']:<5} price=Rs.{data['price']}{flag}")


def total_sales_today():
    today = str(datetime.date.today())
    total = 0
    count = 0
    for s in sales_log:
        if s["date"] == today:
            total += s["total"]
            count += 1
    print(f"\ntoday's sales: {count} transactions, Rs.{total:.2f}")
    return total


def get_low_stock_items():
    low = []
    for iid, data in items.items():
        if data["qty"] < LOW_STOCK:
            low.append((iid, data["name"], data["qty"]))
    return low


def search_item(keyword):
    results = []
    kw = keyword.lower()
    for iid, data in items.items():
        if kw in data["name"].lower():
            results.append((iid, data))
    return results


def most_sold():
    # count from sales log, bit slow but whatever
    counts = {}
    for s in sales_log:
        n = s["name"]
        counts[n] = counts.get(n, 0) + s["qty"]
    if not counts:
        print("no sales yet")
        return
    # sort descending
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    print("\nmost sold items:")
    for name, qty in ranked[:5]:
        print(f"  {name}: {qty} units")


def remove_item(item_id):
    if item_id not in items:
        print("not found, nothing removed")
        return
    name = items[item_id]["name"]
    del items[item_id]
    print(f"removed {name} from inventory")


def update_price(item_id, new_price):
    if item_id not in items:
        print("item not found")
        return
    old = items[item_id]["price"]
    items[item_id]["price"] = new_price
    print(f"price updated: {items[item_id]['name']} Rs.{old} -> Rs.{new_price}")


if __name__ == "__main__":
    # test data - stuff from our college store
    add_item("P001", "Classmate Notebook", 45, 35)
    add_item("P002", "Reynolds Pen", 200, 10)
    add_item("P003", "Stapler", 12, 120)
    add_item("P004", "A4 Sheets (500)", 8, 280)  # this is low stock already
    add_item("P005", "Highlighter Set", 30, 65)
    add_item("P006", "Geometry Box", 5, 150)  # also low
    add_item("P007", "Whiteboard Marker", 25, 30)

    show_inventory()

    sell_item("P001", 5)
    sell_item("P002", 50)
    sell_item("P001", 3)
    sell_item("P002", 30)
    sell_item("P003", 3)
    sell_item("P004", 2)
    sell_item("P006", 3)  # should warn - goes to 2

    print("\nafter sales:")
    show_inventory()

    total_sales_today()

    restock("P004", 50)
    restock("P006", 20)

    print("\nafter restock:")
    show_inventory()

    most_sold()

    print("\nlow stock alert:")
    lows = get_low_stock_items()
    if lows:
        for iid, name, qty in lows:
            print(f"  {iid} {name}: only {qty} left")
    else:
        print("  all good")

    print("\nsearch 'marker':", search_item("marker"))

    update_price("P002", 12)
    remove_item("P003")
    show_inventory()