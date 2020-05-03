<?php

include 'auth.php';

if($_POST['security_key'] == $security_key){
    
    if(isset($_POST['data_key']) and isset($_POST['file_name'])) {  
        #echo $_POST['data_key'];
        

        $conn = new mysqli($servername, $username, $password, $dbname);
        if($conn->connect_error){
            die("connection failed: " . $conn->connect_error);
        }      
        if ($stmt = $conn->prepare("SELECT data_key FROM time WHERE file_name=?")) { 

            $stmt->bind_param("s", $file_name); 
            $file_name= $_POST['file_name']; 
            $stmt->execute(); 
            $stmt->bind_result($got_data_key);
            
            if($stmt->fetch()){
                if ($got_data_key == $_POST['data_key'] and file_exists($main_upload_dir . $_POST['file_name'])) echo "True";
                else echo "False";
            } else echo "False";
            
    
            $stmt->close(); 
            
        }
        $conn->close(); 
            
    }

    else if(isset($_POST['data_key'])) {  
        #echo $_POST['data_key'];
        $conn = new mysqli($servername, $username, $password, $dbname);
        if($conn->connect_error){
            die("connection failed: " . $conn->connect_error);
        }      
        if ($stmt = $conn->prepare("SELECT COUNT(1) FROM time WHERE data_key=?")) { 

            $stmt->bind_param("s", $data_key); 
            $data_key = $_POST['data_key']; 
            $stmt->execute(); 
            
            $stmt->bind_result($got_count);
            
            if($stmt->fetch()){
                echo $got_count;
            } else echo 0;
            
    
            $stmt->close(); 
            
        }
        $conn->close(); 
            
    }

}
?>