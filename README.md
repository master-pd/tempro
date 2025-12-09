# 🌟 Tempro Pro Bot

<div align="center">

![Tempro Bot Banner](https://img.shields.io/badge/Tempro-Pro_Bot-blueviolet)
![Version](https://img.shields.io/badge/Version-3.1.0-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0)
![License](https://img.shields.io/badge/License-MIT-green)

**প্রফেশনাল টেম্পোরারি ইমেইল টেলিগ্রাম বট**  
*বাংলা ইন্টারফেস - ইংলিশ টার্মিনাল*

[🏠 Home](#-tempro-pro-bot) • [🚀 Installation](#-installation) • [📁 Structure](#-project-structure) • [📊 Diagrams](#-architecture-diagrams) • [💡 Usage](#-usage)

</div>

---

## 📋 **টেবিল অফ কন্টেন্ট**

| Section | Description |
|---------|-------------|
| [🌟 Overview](#-overview) | প্রজেক্ট সারসংক্ষেপ |
| [🎯 Features](#-features) | বৈশিষ্ট্যসমূহ |
| [📊 Architecture](#-architecture-diagrams) | আর্কিটেকচার ডায়াগ্রাম |
| [🚀 Installation](#-installation) | ইন্সটলেশন গাইড |
| [📁 Structure](#-project-structure) | প্রজেক্ট স্ট্রাকচার |
| [🔧 Configuration](#-configuration) | কনফিগারেশন |
| [💡 Usage](#-usage) | ব্যবহার নির্দেশিকা |
| [🔄 Flow](#-workflow-diagram) | ওয়ার্কফ্লো ডায়াগ্রাম |
| [📱 Commands](#-telegram-commands) | টেলিগ্রাম কমান্ড |
| [🐛 Troubleshooting](#-troubleshooting) | সমস্যা সমাধান |
| [🤝 Contributing](#-contributing) | কন্ট্রিবিউটিং |
| [📄 License](#-license) | লাইসেন্স |

---

## 🌟 **Overview**

Tempro Pro Bot হলো একটি প্রফেশনাল টেম্পোরারি ইমেইল টেলিগ্রাম বট যার **বাংলা ইউজার ইন্টারফেস** এবং **ইংলিশ ডেভেলপার টার্মিনাল** রয়েছে।

### **🎯 কোর কনসেপ্ট**

┌─────────────────────────────────────────────┐
│ DUAL LANGUAGE SYSTEM │
├─────────────────────────────────────────────┤
│ 🔵 TELEGRAM USER INTERFACE: BENGALI │
│ ⚪ TERMINAL/DEVELOPER VIEW: ENGLISH ONLY │
└─────────────────────────────────────────────┘



---

## 🎯 **Features**

### **📊 Feature Comparison Table**

| Feature | Tempro Basic | Tempro Pro | Description |
|---------|-------------|------------|-------------|
| **Language Support** | Mixed | 🟢 **Dual System** | বাংলা UI + ইংলিশ Terminal |
| **Database** | ❌ No | 🟢 **SQLite** | User stats, email tracking |
| **Rate Limiting** | ❌ No | 🟢 **Advanced** | Per-user & global limits |
| **Inline Menus** | ❌ No | 🟢 **Interactive** | Bengali button menus |
| **Auto Cleanup** | ❌ Manual | 🟢 **Automatic** | 24-hour auto delete |
| **Termux Support** | ❌ Basic | 🟢 **One-click** | `install.sh` script |
| **Logging** | ❌ Basic | 🟢 **Comprehensive** | File + console logs |
| **Backup System** | ❌ No | 🟢 **Automatic** | Database backup |

### **✨ Key Features**

- **🎭 Dual Language System**
  - Telegram: 100% Bengali responses
  - Terminal: 100% English messages
  - No mixing, clean separation

- **🏗️ Professional Architecture**
  - Modular design (MVC pattern)
  - Async/await support
  - Error handling & retry logic

- **📧 Email Features**
  - Generate temporary emails instantly
  - Check inbox in real-time
  - Read full email content
  - HTML to text conversion

- **🛡️ Security & Limits**
  - Rate limiting per user
  - Auto cleanup after 24h
  - No sensitive data storage
  - Public API usage (1secmail.com)

- **📱 User Experience**
  - Inline keyboard menus
  - User statistics (/stats)
  - Activity logging
  - Help system in Bengali

---

## 📊 **Architecture Diagrams**

### **1. 🏗️ System Architecture**

```mermaid
graph TB
    A[User on Telegram] --> B[Telegram API]
    B --> C[Bot Handlers - Bengali]
    C --> D{Command Router}
    
    D --> E[/start - Welcome]
    D --> F[/get - New Email]
    D --> G[/check - Inbox]
    D --> H[/read - Read Email]
    
    E --> I[Menu Manager]
    F --> J[Email API]
    G --> J
    H --> J
    
    J --> K[1secmail.com API]
    
    subgraph "Database Layer"
        L[SQLite DB]
        M[Users Table]
        N[Emails Table]
        O[Messages Table]
    end
    
    I --> L
    J --> L
    
    subgraph "Utility Layer"
        P[Rate Limiter]
        Q[Logger]
        R[Config Manager]
    end
    
    C --> P
    C --> Q
    J --> Q
```