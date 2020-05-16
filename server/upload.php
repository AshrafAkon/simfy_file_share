<?php

include 'auth.php';
//and ($_FILES['split_file']['error'] == 1) 

//header("Access-Control-Allow-Origin: *");
//header("Access-Control-Allow-Headers: Content-Type");
//header("Content-Type: application/json");
//$post_json = file_get_contents("php://input");
//$_POST = json_decode($post_json, true);

if($_POST['security_key'] == $security_key){

    if(isset($_FILES['split_file']) and ($_FILES['split_file']['error'] == 0) and isset($_POST['id']) and isset($_POST['file_name']) and 
    isset($_POST['data_key'])) {
        
        $conn = new mysqli($servername, $username, $password, $dbname);
        if($conn->connect_error){
            die("connection failed: " . $conn->connect_error);
        }
        if($stmt_to_entry_data = $conn->prepare("INSERT INTO time (id, file_name, data_key) VALUES(?, ?, ?)")){
            $stmt_to_entry_data->bind_param("iss", $id, $file_name, $data_key);
            $data_key = $_POST['data_key']; //it has to be unique to thar file
            $file_name = $_POST['file_name']; //file name is a unique hash
            $id = $_POST['id'];
            //echo $_POST['file_name'];
            $file_temp = $_FILES['split_file']['tmp_name'];
            $target_file = $main_upload_dir . basename($file_name);
            $stmt_to_entry_data->execute();
            $stmt_to_entry_data->close();
            $conn->close();
        }
        if (!file_exists($main_upload_dir .$_POST['file_name'])){ 

            if($_FILES['split_file']['size'] > 0){
                move_uploaded_file($file_temp, $target_file);
            }
            
            echo basename($file_name);
        } else {
            echo 'file_exists';
            #echo $main_upload_dir . $_POST['file_name'];
        }
    }
 
}
?>