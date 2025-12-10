# Tempro Bot API Documentation

## Overview
Tempro Bot uses 1secmail.com API for temporary email generation and management.

## 1secmail API Reference

### Base URL https://www.1secmail.com/api/v1/


### Available Endpoints

#### 1. Get Domain List

GET ?action=getDomainList


**Response:**
```json
[
  "1secmail.com",
  "1secmail.org",
  "1secmail.net",
  "wwjmp.com",
  "esiix.com",
  "xojxe.com",
  "yoggm.com"
]

2. Generate Random Email

GET ?action=genRandomMailbox&count=1

Response: 
[
  "random123@1secmail.com"
]

3. Check Mailbox

GET ?action=getMessages&login=LOGIN&domain=DOMAIN

Parameters:

- login: Email username (before @)

- domain: Email domain (after @)

Response:

[
  {
    "id": 123456,
    "from": "sender@example.com",
    "subject": "Test Email",
    "date": "2024-01-01 12:00:00"
  }
]

4. Read Message

GET ?action=readMessage&login=LOGIN&domain=DOMAIN&id=MESSAGE_ID

Response :

{
  "id": 123456,
  "from": "sender@example.com",
  "subject": "Test Email",
  "date": "2024-01-01 12:00:00",
  "attachments": [],
  "body": "Email content here",
  "textBody": "Plain text content",
  "htmlBody": "<p>HTML content</p>"
}

