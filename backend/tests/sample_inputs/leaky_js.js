// leaky_js.js
const fs = require('fs');
const mysql = require('mysql');

const DB_PASSWORD = "supersecret456"; // hardcoded secret

// Resource leak - file handle never closed
function readConfig(filePath) {
    const fd = fs.openSync(filePath, 'r');
    const buffer = Buffer.alloc(1024);
    fs.readSync(fd, buffer, 0, 1024, 0);
    // fd never closed
    return buffer.toString();
}

// SQL Injection
function getUser(userId) {
    const conn = mysql.createConnection({ password: DB_PASSWORD });
    const query = "SELECT * FROM users WHERE id = " + userId;
    conn.query(query, function(err, results) {
        return results;
    });
    // connection never ended
}

// O(n²) inefficiency
function findDuplicates(items) {
    let duplicates = [];
    for (let i = 0; i < items.length; i++) {
        for (let j = 0; j < items.length; j++) {
            if (i !== j && items[i] === items[j]) {
                if (!duplicates.includes(items[i])) {
                    duplicates.push(items[i]);
                }
            }
        }
    }
    return duplicates;
}

// Missing null check
function processUser(user) {
    console.log(user.name.toUpperCase()); // crashes if user or user.name is null
}
