import java.sql.*;
import java.io.*;
import java.util.*;

public class UserService {
    
    // Hardcoded credentials - security issue
    private static final String DB_URL = "jdbc:mysql://localhost:3306/mydb";
    private static final String DB_USER = "root";
    private static final String DB_PASS = "admin123";
    
    // SQL Injection vulnerability
    public static ResultSet getUserByName(String username) throws Exception {
        Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
        Statement stmt = conn.createStatement();
        // Direct string concat - SQL injection
        String query = "SELECT * FROM users WHERE username = '" + username + "'";
        return stmt.executeQuery(query);
    }
    
    // No input validation
    public static void writeToFile(String filename, String content) throws Exception {
        FileWriter fw = new FileWriter(filename);  // Path traversal risk
        fw.write(content);
        fw.close();  // Not in finally block - resource leak
    }

    // Catches generic Exception - bad practice
    public static int divide(int a, int b) {
        try {
            return a / b;  // No check for divide by zero
        } catch (Exception e) {
            e.printStackTrace();  // Exposes stack trace
            return -1;
        }
    }

    // Infinite loop risk
    public static List<Integer> getEvenNumbers(int limit) {
        List<Integer> result = new ArrayList<>();
        int i = 0;
        while (i < limit) {
            if (i % 2 == 0) result.add(i);
            // forgot i++ - infinite loop!
        }
        return result;
    }

    // Null pointer risk
    public static String getUpperCase(String input) {
        return input.toUpperCase();  // No null check
    }

    public static void main(String[] args) throws Exception {
        ResultSet rs = getUserByName("admin' OR '1'='1");
        writeToFile("../../../etc/passwd", "hacked");
        System.out.println(divide(10, 0));
        System.out.println(getUpperCase(null));
    }
}
