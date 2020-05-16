<?php
include 'auth.php';

//global headers
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: Content-Type");
$post_json = file_get_contents("php://input");
$_POST = json_decode($post_json, true);


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
    //echo $_POST['file_name'];
    if(isset($_POST['file_name']) and isset($_POST['data_key'])) {
        //echo "file name data key";
        if(authenticate_file_name($_POST['data_key'], $_POST['file_name'],
         $servername, $username, $password, $dbname)){
    
            $file = $main_upload_dir. $_POST['file_name'];
            //echo "authincated";
            if (file_exists($file)) {
                //echo "file exists";
                if(isset($_POST['return_file'])){

                    // this headers are required or client 
                    // will not understand the file download properly
                    header('Content-Description: File Transfer');
                    header('Content-Type: application/octet-stream');
                    header('Content-Disposition: attachment; filename="'.basename($file).'"');
                    header('Expires: 0');
                    header('Cache-Control: must-revalidate');
                    header('Pragma: public');
                    header('Content-Length: ' . filesize($file));
                    // header content-encoding is set to be none.
                    // otherwise xmlhttprequest.onprogress will 
                    // set onprogress event.lengthcompuatable to false
                    // see more at : https://stackoverflow.com/a/49580828
                    header("Content-Encoding: none");
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