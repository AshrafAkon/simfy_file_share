### Server setup steps

1. Upload the available files in this folder in your server.
2. Create a mysql database. then execute the following two commands
    to create required tables.

 ``` 
    CREATE TABLE info_dict_table ( id INT AUTO_INCREMENT PRIMARY KEY,
    data_key VARCHAR(255) NOT NULL UNIQUE, info_dict MEDIUMTEXT NOT NULL );
```
```
    CREATE TABLE time ( id_serial bigint(20) AUTO_INCREMENT PRIMARY KEY,
    id INT NOT NULL, file_name VARCHAR(255) NOT NULL UNIQUE, 
    data_key VARCHAR(255) NOT NULL, time_uploaded TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ); 
```

3. Create a folder outside webroot (so that its not publicly available
   through website.).
4. Edit `auth.php` with your configuration. 
```
        $servername = url of your server
        $username = your mysql username
        $password = your mysql password
        $dbname = your mysql database name
        $main_upload_dir = full path of the folder created in step 3
        $security_key = choose a secure security key. make sure they both match on client side 
```

