<?php

include 'auth.php';
//do not use error reporting in public server
//mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);

//$stmt_revive = $conn->prepare("SELECT info_dict from info_dict_table where data_key = ?");
//$stmt_revive->bind_param("s", $data_key);


if($_POST['security_key'] == $security_key){

    if(isset($_POST['download_info_dict']) and isset($_POST['data_key'])){  
        $conn = new mysqli($servername, $username, $password, $dbname);
        if($conn->connect_error){
            die("connection failed: " . $conn->connect_error);
        }      
        if ($stmt = $conn->prepare("SELECT info_dict from info_dict_table where data_key = ?")) { 

            $stmt->bind_param("s", $tt2); 
            $tt2 = $_POST['data_key']; 
            $stmt->execute(); 
            
            $stmt->bind_result($got_info_dict);
            
            if($stmt->fetch()){
                echo $got_info_dict;
            }
            
    
            $stmt->close();
            
            
        }
        $conn->close();   
        
    }

    else if(isset($_POST['info_dict']) and isset($_POST['data_key'])){  
        $conn = new mysqli($servername, $username, $password, $dbname);
        if($conn->connect_error){
            die("connection failed: " . $conn->connect_error);
        }
        // $stmt_to_entry_data =
        $data_key = $_POST['data_key']; 
        $info_dict = $_POST['info_dict'];
        //die('prepare() failed: ' . htmlspecialchars($mysqli->error));
        
        #echo  $stmt_to_entry_data;
        if($stmt_to_entry_data = $conn->prepare("INSERT INTO info_dict_table (data_key) VALUES(?)")){
            $stmt_to_entry_data->bind_param("s", $data_key);
                //echo "doing ";
            
            $stmt_to_entry_data->execute();

            $stmt_to_entry_data->bind_param("s", $data_key);
            //echo "doing ";
            $data_key = $_POST['data_key']; 
            $stmt_to_entry_data->execute();
            $stmt_to_entry_data->close();
        } 

        if($stmt_to_entry_info_dict= $conn->prepare("UPDATE info_dict_table SET info_dict=? WHERE data_key = ?")){
            $stmt_to_entry_info_dict->bind_param("ss", $info_dict , $data_key);
            
            $stmt_to_entry_info_dict->execute();
            $stmt_to_entry_info_dict->close();
        }
        $conn->close(); 

    }
    
    
}
?>