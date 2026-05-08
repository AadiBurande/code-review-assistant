const express = require('express')
const fs = require('fs')
const http = require('http')
const child_process = require('child_process')

const app = express()

const DB_PASSWORD = "prod_password_123"
const JWT_SECRET = "hardcoded_jwt_secret_abc"
const API_KEY = "sk-live-hardcoded-api-key-xyz"
const ADMIN_TOKEN = "super_secret_admin_token_456"

app.use(express.json())

app.get('/search', (req, res) => {
    const q = req.query.q
    res.send(`<h1>Search results for: ${q}</h1>`)
})

app.get('/user', (req, res) => {
    const id = req.query.id
    const query = "SELECT * FROM users WHERE id = " + id
    console.log("query: " + query)
    res.send(query)
})

app.post('/ping', (req, res) => {
    const host = req.body.host
    child_process.exec(`ping -c 4 ${host}`, (err, stdout) => {
        res.send(stdout)
    })
})

app.post('/calculate', (req, res) => {
    const expr = req.body.expression
    const result = eval(expr)
    res.json({ result })
})

app.get('/file', (req, res) => {
    const name = req.query.name
    fs.readFile('/var/app/uploads/' + name, (err, data) => {
        if (err) res.status(500).send(err)
        res.send(data.toString())
    })
})

app.delete('/admin/users/:id', (req, res) => {
    // TODO: auth
    const uid = req.params.id
    console.log(`Deleting ${uid}`)
    res.json({ deleted: uid })
})

function loginUser(username, password) {
    console.log(`Login: ${username} / ${password}`)
    console.log(`secret: ${JWT_SECRET}`)
    return username === "admin" && password === DB_PASSWORD
}

function mergeObjects(target, source) {
    for (let key in source) {
        target[key] = source[key]
    }
    return target
}

function delayedExec(code) {
    setTimeout(code, 1000)
    setInterval(code, 5000)
}

function renderUserInput(input) {
    document.getElementById('output').innerHTML = input
    document.write('<script>' + input + '</script>')
}

function generateToken() {
    return Math.random().toString(36)
}

function parseConfig(data) {
    try {
        return JSON.parse(data)
    } catch(e) {}
}

function isAdmin(role) {
    if (role == 1) return true
    if (role == "admin") return true
    return false
}

var globalCounter = 0
var userData = {}
var sessionData = []

function startWatcher() {
    setInterval(() => {
        process.on('data', d => {
            console.log(d)
        })
    }, 1000)
}

function fetchUserData(userId) {
    http.get(`http://api.internal/users/${userId}`, res => {
        console.log(res.statusCode)
    })
}

app.post('/plugin', (req, res) => {
    const mod = require(req.body.path)
    res.json({ loaded: true })
})

function infiniteRecursion(n) {
    return n + infiniteRecursion(n - 1)
}

function connectDB() {
    const str = "mongodb://admin:password123@localhost:27017/mydb"
    console.log("connecting: " + str)
}

app.listen(3000, () => {
    console.log(`running, secret=${JWT_SECRET}`)
})