// CanteenBill.java
// canteen billing for TCET - handles orders, gst, discount
// made this in one sitting after lab, might have bugs
// priya said to add combo offers but skipping for now

import java.util.*;

public class CanteenBill {

    // menu - item name -> price
    // hardcoded for now, canteen uncle gave me this list lol
    static HashMap<String, Double> menu = new HashMap<>();
    static ArrayList<String[]> orders = new ArrayList<>();  // each order = [tableNo, item, qty]
    static HashMap<String, Double> tableTotal = new HashMap<>();

    static double GST = 5.0;  // 5% for food
    static double DISCOUNT_THRESHOLD = 200.0;  // get discount if bill > 200
    static double DISCOUNT_PCT = 10.0;

    public static void main(String args[]) {
        loadMenu();

        System.out.println("menu loaded: " + menu.size() + " items");
        printMenu();

        // simulate some orders from different tables
        placeOrder("T1", "Vada Pav", 3);
        placeOrder("T1", "Chai", 2);
        placeOrder("T2", "Samosa", 4);
        placeOrder("T2", "Cold Coffee", 1);
        placeOrder("T3", "Maggi", 2);
        placeOrder("T3", "Vada Pav", 1);
        placeOrder("T1", "Samosa", 2);  // T1 ordering again
        placeOrder("T4", "Sandwich", 1);
        placeOrder("T4", "Chai", 3);
        placeOrder("T5", "Cold Coffee", 2);
        placeOrder("T5", "Maggi", 1);

        System.out.println("\n--- generating bills ---");
        generateBill("T1");
        generateBill("T2");
        generateBill("T3");

        System.out.println("\nall table totals so far:");
        for (String t : tableTotal.keySet()) {
            System.out.println("  " + t + " -> Rs." + tableTotal.get(t));
        }

        System.out.println("\ntotal canteen collection: Rs." + totalCollection());

        System.out.println("\nbest seller:");
        findBestSeller();
    }

    static void loadMenu() {
        menu.put("Vada Pav",    12.0);
        menu.put("Samosa",       8.0);
        menu.put("Chai",         7.0);
        menu.put("Cold Coffee", 30.0);
        menu.put("Maggi",       25.0);
        menu.put("Sandwich",    35.0);
        menu.put("Poha",        20.0);
        menu.put("Juice",       40.0);
    }

    static void printMenu() {
        System.out.println("\n== TCET Canteen Menu ==");
        for (String item : menu.keySet()) {
            System.out.println("  " + item + " - Rs." + menu.get(item));
        }
    }

    static void placeOrder(String tableNo, String item, int qty) {
        if (!menu.containsKey(item)) {
            System.out.println("item not available: " + item);
            return;
        }
        if (qty <= 0) {
            System.out.println("qty should be positive");
            return;
        }
        // store as string array - not the cleanest but works
        orders.add(new String[]{tableNo, item, String.valueOf(qty)});
        System.out.println("order placed: T=" + tableNo + " | " + qty + "x " + item);
    }

    static void generateBill(String tableNo) {
        System.out.println("\n--- Bill for " + tableNo + " ---");

        double subtotal = 0;
        boolean hasOrders = false;

        for (String[] order : orders) {
            if (!order[0].equals(tableNo)) continue;

            String item = order[1];
            int qty = Integer.parseInt(order[2]);
            double price = menu.get(item);
            double lineTotal = price * qty;
            subtotal += lineTotal;
            hasOrders = true;

            System.out.println("  " + qty + "x " + item + " @ Rs." + price + " = Rs." + lineTotal);
        }

        if (!hasOrders) {
            System.out.println("  no orders for this table");
            return;
        }

        // apply discount if applicable
        double discountAmt = 0;
        if (subtotal > DISCOUNT_THRESHOLD) {
            // BUG: discount calculated on subtotal but applied before GST
            // should ideally be after GST or make it clear which base
            discountAmt = subtotal * DISCOUNT_PCT / 100;
            System.out.println("  Discount (" + DISCOUNT_PCT + "%): -Rs." + discountAmt);
        }

        double afterDiscount = subtotal - discountAmt;
        // BUG: GST on discounted amount but label says "GST on total"
        double gstAmt = afterDiscount * GST / 100;

        double finalBill = afterDiscount + gstAmt;

        System.out.println("  ----");
        System.out.println("  Subtotal : Rs." + subtotal);
        System.out.println("  GST (5%) : Rs." + gstAmt);
        System.out.println("  TOTAL    : Rs." + finalBill);

        // update table running total
        // BUG: this overwrites if generateBill called twice for same table
        tableTotal.put(tableNo, finalBill);
    }

    static double totalCollection() {
        double total = 0;
        for (double amt : tableTotal.values()) {
            total += amt;
        }
        return total;
    }

    static void findBestSeller() {
        HashMap<String, Integer> itemCount = new HashMap<>();

        for (String[] order : orders) {
            String item = order[1];
            int qty = Integer.parseInt(order[2]);
            if (itemCount.containsKey(item)) {
                itemCount.put(item, itemCount.get(item) + qty);
            } else {
                itemCount.put(item, qty);
            }
        }

        String best = null;
        int max = 0;
        for (String item : itemCount.keySet()) {
            // BUG: if two items have same count, last one wins
            if (itemCount.get(item) > max) {
                max = itemCount.get(item);
                best = item;
            }
        }

        if (best != null) {
            System.out.println("  " + best + " (" + max + " units sold)");
        }
    }

    static void clearTable(String tableNo) {
        // removes orders but NOT from tableTotal - inconsistent state possible
        orders.removeIf(o -> o[0].equals(tableNo));
        System.out.println("cleared orders for " + tableNo);
    }

    static int countTablesActive() {
        HashSet<String> active = new HashSet<>();
        for (String[] o : orders) {
            active.add(o[0]);
        }
        return active.size();
    }

    static void addMenuItem(String name, double price) {
        if (price < 0) {
            System.out.println("price cant be negative");
            return;
        }
        // no check if item already exists - silently overwrites
        menu.put(name, price);
        System.out.println("added to menu: " + name + " Rs." + price);
    }
}