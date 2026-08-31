import sqlite3
import time
import uuid

def setup_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE subdomains (
            id INTEGER PRIMARY KEY,
            scan_id TEXT,
            subdomain TEXT,
            is_alive BOOLEAN
        )
    """)
    conn.commit()
    return conn

def test_n_plus_1(conn, subdomains, live_hosts, scan_id):
    cursor = conn.cursor()
    start = time.time()
    for subdomain in subdomains:
        if subdomain.strip():
            is_alive = subdomain in live_hosts
            cursor.execute("""
                INSERT INTO subdomains (scan_id, subdomain, is_alive)
                VALUES (?, ?, ?)
            """, (scan_id, subdomain, is_alive))
    conn.commit()
    end = time.time()
    return end - start

def test_executemany(conn, subdomains, live_hosts, scan_id):
    cursor = conn.cursor()
    start = time.time()

    # Using generator expression for executemany
    # Wait, need to convert to boolean maybe, sqlite handles bools as 0/1
    data = (
        (scan_id, subdomain, subdomain in live_hosts)
        for subdomain in subdomains
        if subdomain.strip()
    )
    cursor.executemany("""
        INSERT INTO subdomains (scan_id, subdomain, is_alive)
        VALUES (?, ?, ?)
    """, data)

    conn.commit()
    end = time.time()
    return end - start

def main():
    print("Generating test data (100,000 subdomains)...")
    subdomains = [f"sub{i}.example.com" for i in range(100000)]
    live_hosts = set([f"sub{i}.example.com" for i in range(0, 100000, 5)]) # 20% live
    scan_id = str(uuid.uuid4())

    print("Testing N+1 (Baseline)...")
    conn1 = setup_db()
    time_n_plus_1 = test_n_plus_1(conn1, subdomains, live_hosts, scan_id)
    print(f"N+1 time: {time_n_plus_1:.4f} seconds")

    print("Testing executemany (Optimized)...")
    conn2 = setup_db()
    time_executemany = test_executemany(conn2, subdomains, live_hosts, scan_id)
    print(f"executemany time: {time_executemany:.4f} seconds")

    speedup = time_n_plus_1 / time_executemany if time_executemany > 0 else float('inf')
    improvement = (time_n_plus_1 - time_executemany) / time_n_plus_1 * 100
    print(f"Speedup: {speedup:.2f}x")
    print(f"Improvement: {improvement:.2f}%")

if __name__ == '__main__':
    main()
