const express = require('express');
const fs = require('fs');
const http = require('http'); // should use https
const child_process = require('child_process');
const app = express();

// Hardcoded secrets - Critical
const DB_PASSWORD = "prod_password_123";
const JWT_SECRET = "hardcoded_jwt_secret_abc";
const API_KEY = "sk-live-hardcoded-api-key-xyz";
const ADMIN_TOKEN = "super_secret_admin_token_456";

app.use(express.json());

// XSS - direct user input into HTML response
app.get('/search', (req, res) => {
    const query = req.query.q;
    res.send(`<h1>Search results for: ${query}</h1>`); // no sanitization
});

// SQL Injection - string concatenation in query
app.get('/user', (req, res) => {
    const userId = req.query.id;
    const query = "SELECT * FROM users WHERE id = " + userId; // SQL injection
    console.log("Running query: " + query);
    res.send(query);
});

// Command Injection via exec
app.post('/ping', (req, res) => {
    const host = req.body.host;
    child_process.exec(`ping -c 4 ${host}`, (err, stdout) => { // command injection
        res.send(stdout);
    });
});

// eval() usage - code injection
app.post('/calculate', (req, res) => {
    const expr = req.body.expression;
    const result = eval(expr); // arbitrary code execution
    res.json({ result });
});

// Path traversal - no sanitization
app.get('/file', (req, res) => {
    const filename = req.query.name;
    fs.readFile('/var/app/uploads/' + filename, (err, data) => { // path traversal
        if (err) res.status(500).send(err);
        res.send(data.toString());
    });
});

// No authentication on admin route
app.delete('/admin/users/:id', (req, res) => {
    // TODO: add authentication
    // FIXME: anyone can delete any user
    const userId = req.params.id;
    console.log(`Deleting user ${userId}`);
    res.json({ deleted: userId });
});

// Password logged in plaintext
function loginUser(username, password) {
    console.log(`Login attempt: ${username} / ${password}`); // password in logs!
    console.log(`Using secret: ${JWT_SECRET}`);
    return username === "admin" && password === DB_PASSWORD;
}

// Prototype pollution
function mergeObjects(target, source) {
    for (let key in source) {
        target[key] = source[key]; // no hasOwnProperty check
    }
    return target;
}

// setTimeout with string - eval equivalent
function delayedExec(code) {
    setTimeout(code, 1000); // string passed to setTimeout
    setInterval(code, 5000); // string passed to setInterval
}

// innerHTML assignment - XSS
function renderUserInput(userInput) {
    document.getElementById('output').innerHTML = userInput; // XSS
    document.write('<script>' + userInput + '</script>'); // XSS
}

// Weak random for security token
function generateToken() {
    return Math.random().toString(36); // not cryptographically secure
}

// Empty catch block
function parseConfig(data) {
    try {
        return JSON.parse(data);
    } catch(e) {
        // swallowed silently
    }
}

// Loose equality bugs
function isAdmin(role) {
    if (role == 1) { // loose equality
        return true;
    }
    if (role == "admin") { // loose equality
        return true;
    }
    return false;
}

// var instead of const/let
var globalCounter = 0;
var userData = {};
var sessionData = [];

// Memory leak - listener added in loop
function startWatcher() {
    setInterval(() => {
        process.on('data', (d) => { // new listener added every second
            console.log(d);
        });
    }, 1000);
}

// Insecure HTTP request
function fetchUserData(userId) {
    http.get(`http://api.internal/users/${userId}`, (res) => { // plain HTTP
        console.log(res.statusCode);
    });
}

// Dynamic require with user input
app.post('/plugin', (req, res) => {
    const plugin = req.body.name;
    const mod = require(req.body.path); // dynamic require - code injection
    res.json({ loaded: true });
});

// Recursive function without base case
function infiniteRecursion(n) {
    return n + infiniteRecursion(n - 1); // stack overflow
}

// Credentials in URL
function connectDB() {
    const connStr = "mongodb://admin:password123@localhost:27017/mydb"; // creds in URL
    console.log("Connecting to: " + connStr);
}

app.listen(3000, () => {
    console.log(`Server running with secret: ${JWT_SECRET}`); // secret in logs
});
