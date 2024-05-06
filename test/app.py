import streamlit as st
import sqlite3  # For SQLite database connection
import datetime  # For timestamps
# Database connection details (replace with your desired path)
db_path = "access_log.db"

def create_connection():
  """Creates a connection to the SQLite database."""
  conn = None
  try:
    conn = sqlite3.connect(db_path)
    print("Connected to SQLite database.")
  except sqlite3.Error as e:
    print(f"Error connecting to database: {e}")
  return conn

def create_table(conn):
  """Creates the 'access_logs' table if it doesn't exist."""
  cursor = conn.cursor()
  cursor.execute('''CREATE TABLE IF NOT EXISTS access_logs (
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      log_message TEXT
                    )''')
  conn.commit()

def store_log(conn, message):
  """Stores a new log message in the database (if connection provided)."""
  if conn is not None:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO access_logs (log_message) VALUES (?)", (message,))
    conn.commit()
  else:
    print("Error! Could not store log message (no connection).")

def main():
  """Main function for the Streamlit app."""
  # Select version from dropdown (replace with your desired version names)
  version_options = ["Version 1", "Version 2", "Version 3 (Database Log)"]
  selected_version = st.selectbox("Select Version", version_options)

  # Get database connection using 'with' statement (recommended)
  with create_connection() as conn:
    create_table(conn)  # Create table within the 'with' block

    # Handle specific version functionalities
    if selected_version == "Version 1":
      # Your Version 1 content here (e.g., display sample text)
      st.title('Simple Text App')
      st.write("Hello, World!")

    elif selected_version == "Version 2":
      # Your Version 2 content here (e.g., display OS information)
      import psutil  # Library for CPU usage

      def get_cpu_info():
        """Fetches CPU usage."""
        cpu_usage = psutil.cpu_percent()
        return cpu_usage

      st.title('System CPU Information')
      cpu_usage = get_cpu_info()
      st.metric("CPU Usage", f"{cpu_usage}%")

    elif selected_version == "Version 3 (Database Log)":
      # Store access log on app load
      current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      store_log(conn, f"Access at: {current_time}")

      # Your Version 3 content here (if any)
      st.title('Access Logged App')
      # ... (add your app elements)

if __name__ == '__main__':
  main()

