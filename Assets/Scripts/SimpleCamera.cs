using UnityEngine;

/// <summary>
/// Simple camera controller for navigating the LiDAR point cloud scene.
/// Attach to Main Camera GameObject.
/// </summary>
public class SimpleCamera : MonoBehaviour
{
    [Header("Movement")]
    public float moveSpeed = 5f;
    public float fastMoveSpeed = 10f;
    public float slowMoveSpeed = 2f;
    
    [Header("Look")]
    public float lookSpeed = 2f;
    public float lookSpeedMouse = 3f;
    
    [Header("Smoothing")]
    public bool smoothMovement = true;
    public float smoothTime = 0.1f;
    
    private Vector3 _velocity = Vector3.zero;
    private Vector2 _rotation = Vector2.zero;
    
    void Start()
    {
        // Store initial rotation
        _rotation.y = transform.eulerAngles.y;
        _rotation.x = transform.eulerAngles.x;
    }
    
    void Update()
    {
        HandleMovement();
        HandleRotation();
    }
    
    void HandleMovement()
    {
        // Get input
        float h = Input.GetAxis("Horizontal");  // A/D or Left/Right
        float v = Input.GetAxis("Vertical");    // W/S or Up/Down
        float y = 0;
        
        // Vertical movement
        if (Input.GetKey(KeyCode.E) || Input.GetKey(KeyCode.Space)) 
            y = 1;
        if (Input.GetKey(KeyCode.Q) || Input.GetKey(KeyCode.LeftControl)) 
            y = -1;
        
        // Determine speed
        float speed = moveSpeed;
        if (Input.GetKey(KeyCode.LeftShift)) 
            speed = fastMoveSpeed;
        if (Input.GetKey(KeyCode.LeftAlt)) 
            speed = slowMoveSpeed;
        
        // Calculate movement direction
        Vector3 moveDirection = new Vector3(h, y, v);
        
        // Apply speed and deltaTime
        Vector3 targetPosition = transform.position + transform.TransformDirection(moveDirection) * speed * Time.deltaTime;
        
        // Smooth or instant movement
        if (smoothMovement)
        {
            transform.position = Vector3.SmoothDamp(transform.position, targetPosition, ref _velocity, smoothTime);
        }
        else
        {
            transform.position = targetPosition;
        }
    }
    
    void HandleRotation()
    {
        // Right mouse button for mouse look
        if (Input.GetMouseButton(1))
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
            
            float mouseX = Input.GetAxis("Mouse X") * lookSpeedMouse;
            float mouseY = -Input.GetAxis("Mouse Y") * lookSpeedMouse;
            
            _rotation.x += mouseY;
            _rotation.y += mouseX;
            
            // Clamp vertical rotation to avoid flipping
            _rotation.x = Mathf.Clamp(_rotation.x, -90f, 90f);
            
            transform.eulerAngles = new Vector3(_rotation.x, _rotation.y, 0);
        }
        else
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
        
        // Alternative: Arrow keys for rotation
        if (Input.GetKey(KeyCode.LeftArrow))
        {
            _rotation.y -= lookSpeed;
        }
        if (Input.GetKey(KeyCode.RightArrow))
        {
            _rotation.y += lookSpeed;
        }
        if (Input.GetKey(KeyCode.UpArrow))
        {
            _rotation.x += lookSpeed;
        }
        if (Input.GetKey(KeyCode.DownArrow))
        {
            _rotation.x -= lookSpeed;
        }
        
        // Clamp vertical rotation
        _rotation.x = Mathf.Clamp(_rotation.x, -90f, 90f);
        
        transform.eulerAngles = new Vector3(_rotation.x, _rotation.y, 0);
    }
    
    void OnGUI()
    {
        // Show controls hint
        GUI.Label(new Rect(10, Screen.height - 100, 400, 20), "Camera Controls:");
        GUI.Label(new Rect(10, Screen.height - 80, 400, 20), "WASD/Arrows: Move | E/Q: Up/Down");
        GUI.Label(new Rect(10, Screen.height - 60, 400, 20), "Right Mouse: Look Around");
        GUI.Label(new Rect(10, Screen.height - 40, 400, 20), "Shift: Fast | Alt: Slow");
    }
}
