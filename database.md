```sql
USE pinnacle_app;

-- Table for visitor statistics
CREATE TABLE visitor_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    visitors_today INT DEFAULT 0,
    visitors_yesterday INT DEFAULT 0,
    visitors_this_week INT DEFAULT 0,
    visitors_this_month INT DEFAULT 0,
    total_visitors INT DEFAULT 0,
);

-- Table for user reviews
CREATE TABLE user_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    review TEXT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

```sql
-- Table for visitor logs
CREATE TABLE visitor_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    visit_date DATE NOT NULL,
    UNIQUE (ip_address, user_agent(255), visit_date)
);
```


```sql
-- Table for online users
CREATE TABLE online_users (
    session_id VARCHAR(255) PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```