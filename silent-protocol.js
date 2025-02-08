const axios = require('axios');
const fs = require('fs/promises');
const TelegramBot = require('node-telegram-bot-api');
const { SocksProxyAgent } = require('socks-proxy-agent');
const { HttpsProxyAgent } = require('https-proxy-agent');

// Constants
const ENDPOINTS = {
    POSITION: 'https://ceremony-backend.silentprotocol.org/ceremony/position',
    PING: 'https://ceremony-backend.silentprotocol.org/ceremony/ping'
};

const FILES = {
    TOKENS: 'tokens.txt',
    CONFIG: 'config.json',
    PROXIES: 'proxies.txt'
};

const UPDATE_INTERVALS = {
    POSITION: 10000,  // 10 seconds
    NOTIFICATION: 60000  // 1 minute
};

// Console styling
const ConsoleStyle = {
    reset: '\x1b
