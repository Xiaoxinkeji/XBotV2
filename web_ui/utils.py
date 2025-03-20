from typing import Any, Dict, Optional, Union

def api_response(
    data: Any = None, 
    success: bool = True, 
    message: Optional[str] = None, 
    status_code: int = 200
) -> Dict[str, Any]:
    """生成一致格式的API响应"""
    response = {
        "success": success
    }
    
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    return response

def error_response(
    message: str, 
    detail: Optional[Union[str, Dict[str, Any]]] = None, 
    status_code: int = 400
) -> Dict[str, Any]:
    """生成错误响应"""
    response = {
        "success": False,
        "message": message
    }
    
    if detail is not None:
        response["detail"] = detail
        
    return response 