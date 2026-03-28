// vulnerable_java.java
import java.sql.*;

public class UserService {

    private static final String DB_PASSWORD = "admin123"; // hardcoded secret

    public User getUser(String userId) throws SQLException {
        Connection conn = DriverManager.getConnection("jdbc:mysql://localhost/db", "root", DB_PASSWORD);
        Statement stmt = conn.createStatement();
        // SQL Injection vulnerability
        String query = "SELECT * FROM users WHERE id = '" + userId + "'";
        ResultSet rs = stmt.executeQuery(query);
        // connection never closed → resource leak
        return null;
    }

    public int[] findDuplicateIndexes(int[] arr) {
        // O(n²) nested loop
        for (int i = 0; i < arr.length; i++) {
            for (int j = 0; j < arr.length; j++) {
                if (i != j && arr[i] == arr[j]) {
                    System.out.println("Duplicate: " + arr[i]);
                }
            }
        }
        return arr;
    }

    public void deleteUser(User user) {
        // missing null check
        String path = "/data/users/" + user.getId();
        System.out.println("Deleting: " + path);
    }
}
