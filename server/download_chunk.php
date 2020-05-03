<?php
include 'auth.php';
function authenticate_file_name($data_key, $file_name,$servername, $username, $password, $dbname) {
    $conn = new mysqli($servername, $username, $password, $dbname);
    if($conn->connect_error){
        die("connection failed: " . $conn->connect_error);
    }
    
    $stmt_revive = $conn->prepare("SELECT data_key from time where file_name = ?");
    $stmt_revive->bind_param("s", $file_name);
    $stmt_revive->execute();
    $stmt_revive->bind_result($got_data_key);
    
    if($stmt_revive->fetch()){
        #echo $got_data_key;
        if($got_data_key == $data_key){
            $stmt_revive->close();
            $conn->close();
            
            return True;
        }
    }
   
    $stmt_revive->close();
    $conn->close();
    return False;
    
}

if($_POST['security_key'] == $security_key){

    if(isset($_POST['file_name']) and isset($_POST['data_key'])) {
        if(authenticate_file_name($_POST['data_key'], $_POST['file_name'], $servername, $username, $password, $dbname)){
        
            $file = $main_upload_dir. $_POST['file_name'];
                
            if (file_exists($file)) {
                if(isset($_POST['return_file'])){
                    header('Content-Description: File Transfer');
                    header('Content-Type: application/octet-stream');
                    header('Content-Disposition: attachment; filename="'.basename($file).'"');
                    header('Expires: 0');
                    header('Cache-Control: must-revalidate');
                    header('Pragma: public');
                    header('Content-Length: ' . filesize($file));
                    readfile($file);
                    exit;
                } else {
                    echo "True";
                }

            } 
        }
        #echo "false";
    }

}
?>