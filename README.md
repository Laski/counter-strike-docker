# CS 1.6 HLDS + AMX MOD X + CSDM


Build & run
-----------

1. Create `.env` configuration file from example file:

    ```
    $ cp example.env .env
    ```

2. Build custom server:
 
    ```
    $ docker-compose build
    ```
    
4. Edit `.env` configuration variables if needed (see image entrypoint file `hlds_run.sh` if you want to figure out how variables are used).

5. Start your server:

    ```
    $ docker-compose up -d
    ```

6. Enjoy ;)
