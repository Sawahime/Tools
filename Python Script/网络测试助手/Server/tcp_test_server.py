import socket
import threading
import time

class TCPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start the TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"TCP Server started on {self.host}:{self.port}")
        print("Waiting for connections...")
        
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                print(f"Received from {client_address}: {data.decode('utf-8')}")
                
                # Echo back the received data
                response = f"ECHO[{time.time()}]: {data.decode('utf-8')}"
                client_socket.sendall(response.encode('utf-8'))
                
        except Exception as e:
            print(f"Client {client_address} error: {e}")
        finally:
            client_socket.close()
            print(f"Connection with {client_address} closed")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("TCP Server stopped")

if __name__ == '__main__':
    server = TCPServer(port=8080)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()