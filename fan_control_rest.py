

if __name__ == "__main__":
    import webui

    data_pin = 22

    debug = False
    app = webui.App(data_pin)

    app.Server.run(host="::", port=8082, debug=debug, reloader=debug)


