def shutdown_server(socket, stop_event):
    stop_event.set()
    socket.close()
