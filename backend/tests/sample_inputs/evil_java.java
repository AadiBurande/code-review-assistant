import java.io.*;
import java.net.*;
import java.security.*;
import java.sql.*;
import java.util.*;

public class evil_java {

    // Hardcoded credentials - Critical security issue
    private static final String DB_URL = "jdbc:mysql://localhost:3306/mydb";
    private static final String DB_USER = "root";
    private static final String DB_PASS = "admin@12345";
    private static final String SECRET_KEY = "hardcoded_jwt_secret_xyz";
    private static final String API_KEY = "sk-prod-hardcoded-key-123456";

    // SQL Injection - No PreparedStatement
    public static ResultSet getUser(String username) throws Exception {
        Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
        Statement stmt = conn.createStatement();
        String query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + DB_PASS + "'";
        return stmt.executeQuery(query);
    }

    // Command Injection via Runtime.exec
    public static String runCommand(String userInput) throws Exception {
        Runtime rt = Runtime.getRuntime();
        Process proc = rt.exec("ping " + userInput);
        BufferedReader stdInput = new BufferedReader(new InputStreamReader(proc.getInputStream()));
        return stdInput.readLine();
    }

    // Weak MD5 hashing for passwords
    public static String hashPassword(String password) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] hash = md.digest(password.getBytes());
        return Base64.getEncoder().encodeToString(hash);
    }

    // Weak SHA-1 for tokens
    public static String generateToken(String data) throws Exception {
        MessageDigest sha = MessageDigest.getInstance("SHA-1");
        return Base64.getEncoder().encodeToString(sha.digest(data.getBytes()));
    }

    // Insecure Random - not cryptographically secure
    public static int generateOTP() {
        Random rand = new Random();
        return rand.nextInt(9999);
    }

    // Path Traversal vulnerability
    public static String readFile(String filename) throws Exception {
        FileReader fr = new FileReader("/var/app/uploads/" + filename);
        BufferedReader br = new BufferedReader(fr);
        return br.readLine();
        // fr and br never closed - resource leak
    }

    // Resource leak - FileWriter not in try-with-resources
    public static void writeLog(String message) throws Exception {
        FileWriter fw = new FileWriter("app.log", true);
        fw.write(message);
        // fw.close() missing - resource leak
    }

    // Empty catch block - exception swallowed
    public static int divide(int a, int b) {
        try {
            return a / b;
        } catch (Exception e) {
            // silently swallowed
        }
        return -1;
    }

    // printStackTrace exposes internals
    public static void processPayment(double amount) {
        try {
            if (amount < 0) throw new Exception("Invalid amount");
        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("Payment failed: " + e.getMessage());
        }
    }

    // Null pointer - no null check
    public static String getUserEmail(String userId) {
        Map<String, String> db = null;
        return db.get(userId).toUpperCase(); // NPE guaranteed
    }

    // Infinite loop - no exit condition
    public static void pollServer() {
        while (true) {
            System.out.println("Polling...");
            // no break or sleep - CPU burn
        }
    }

    // Generic throws Exception - bad practice
    public static void processData(String data) throws Exception {
        if (data == null) throw new Exception("Null data");
        System.out.println(data);
    }

    // Insecure HTTP connection (not HTTPS)
    public static String fetchData(String endpoint) throws Exception {
        URL url = new URL("http://" + endpoint); // should be https
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        return conn.getResponseMessage();
    }

    // System.out instead of logger
    public static void loginUser(String username, String password) {
        System.out.println("Login attempt: " + username + " / " + password); // logs password!
        System.out.println("Secret key used: " + SECRET_KEY);
    }

    // Hardcoded IP address
    public static void connectToServer() throws Exception {
        Socket socket = new Socket("192.168.1.100", 8080);
        System.out.println("Connected to hardcoded IP");
        // socket never closed
    }

    // TODO left in production code
    public static void processOrder(String orderId) {
        // TODO: add authentication check
        // FIXME: this crashes on empty orderId
        // HACK: temporary workaround
        System.out.println("Processing order: " + orderId);
    }

    // Long parameter list
    public static void createUser(String name, String email, String password,
                                   String phone, String address, String city,
                                   String country, String zip, String role,
                                   String department, String manager) {
        System.out.println("Creating user: " + name);
    }

    public static void main(String[] args) throws Exception {
        System.out.println(getUser("admin' OR '1'='1' --"));
        System.out.println(runCommand("google.com && rm -rf /"));
        System.out.println(hashPassword("password123"));
        System.out.println(generateOTP());
        System.out.println(readFile("../../etc/passwd"));
        loginUser("admin", "supersecret123");
        pollServer();
    }
}
