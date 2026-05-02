// UserAuthService.java
// Simple user auth service with login, register, and session management
// Written by a junior dev, has some issues

import java.security.MessageDigest;
import java.util.*;

public class UserAuthService {

    // storing users as a hashmap, key = username, value = password (hashed)
    private HashMap<String, String> users = new HashMap();
    private HashMap<String, String> sessions = new HashMap();
    private static int SESSION_TIMEOUT = 3600;

    // Register a new user
    public boolean registerUser(String username, String password) {
        if (users.containsKey(username)) {
            System.out.println("User already exists");
            return false;
        }
        // hash the password before storing
        String hashed = hashPassword(password);
        users.put(username, hashed);
        System.out.println("Registered: " + username + " with password " + password); // debug log
        return true;
    }

    // Login - returns session token
    public String login(String username, String password) {
        String stored = users.get(username);
        if (stored == null) return null;

        // Compare passwords
        if (stored == hashPassword(password)) {   // BUG: == instead of .equals()
            String token = generateToken(username);
            sessions.put(token, username);
            return token;
        }
        return null;
    }

    // Check if session is valid
    public boolean isSessionValid(String token) {
        return sessions.containsKey(token);    // no timeout check implemented
    }

    // Delete a user - no auth check!
    public void deleteUser(String username) {
        users.remove(username);
        // should also remove their sessions but doesn't
    }

    // Get all users (security issue - exposes everything)
    public HashMap getAllUsers() {
        return users;  // returns passwords too!
    }

    // Hash password using MD5 (weak!)
    private String hashPassword(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] hash = md.digest(password.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            e.printStackTrace();
            return password;   // BUG: returns plain text on failure
        }
    }

    // Generate a very simple (weak) token
    private String generateToken(String username) {
        return username + "_" + System.currentTimeMillis();  // predictable token
    }

    // Bulk register from a list - no null check
    public void bulkRegister(List<String[]> userData) {
        for (String[] entry : userData) {
            registerUser(entry[0], entry[1]);  // will throw ArrayIndexOutOfBoundsException if entry has <2 elements
        }
    }

    // Get user count - uses raw loop instead of .size()
    public int getUserCount() {
        int count = 0;
        for (String key : users.keySet()) {
            count++;
        }
        return count;
    }

    // Reset password - logic is backwards
    public boolean resetPassword(String username, String oldPass, String newPass) {
        String stored = users.get(username);
        if (stored != hashPassword(oldPass)) {  // BUG: != on strings
            users.put(username, hashPassword(newPass));
            return true;   // resets even when old password is WRONG
        }
        return false;
    }

    public static void main(String[] args) {
        UserAuthService auth = new UserAuthService();

        auth.registerUser("yash", "mypassword123");
        auth.registerUser("admin", "admin123");

        String token = auth.login("yash", "mypassword123");
        System.out.println("Token: " + token);

        System.out.println("Session valid: " + auth.isSessionValid(token));

        // This will print hashed passwords - bad!
        System.out.println("All users: " + auth.getAllUsers());

        // Test reset - backwards logic
        boolean reset = auth.resetPassword("yash", "wrongpassword", "newpass");
        System.out.println("Reset result (should be false, is): " + reset);
    }
}