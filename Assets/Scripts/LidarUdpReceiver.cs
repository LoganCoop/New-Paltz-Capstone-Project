using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

public class LidarUdpReceiver : MonoBehaviour
{
    [Serializable]
    public class Packet
    {
        public double t;
        public float dist_cm;
        public int strength;
        public float temp_c;
        public float qw, qx, qy, qz;
    }

    public int port = 5005;
    public Transform pointPrefab;
    public float scaleMeters = 0.01f;
    public int maxPoints = 5000;

    private UdpClient _client;
    private Thread _thread;
    private bool _running;
    private readonly object _lock = new object();
    private Packet _latest;

    private Quaternion _calibration = Quaternion.identity;
    private bool _hasCalibration;

    void Start()
    {
        _client = new UdpClient(port);
        _client.Client.ReceiveTimeout = 250;
        _running = true;
        _thread = new Thread(ReceiveLoop) { IsBackground = true };
        _thread.Start();
    }

    void ReceiveLoop()
    {
        var endPoint = new IPEndPoint(IPAddress.Any, port);
        while (_running)
        {
            try
            {
                var data = _client.Receive(ref endPoint);
                var json = Encoding.UTF8.GetString(data);
                var packet = JsonUtility.FromJson<Packet>(json);
                if (packet == null) continue;

                lock (_lock)
                {
                    _latest = packet;
                }
            }
            catch (SocketException)
            {
                // Timeout to allow thread to exit cleanly.
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch
            {
            }
        }
    }

    void Update()
    {
        if (IsCalibrationPressed())
        {
            Packet snapshot;
            lock (_lock)
            {
                snapshot = _latest;
            }

            if (snapshot != null)
            {
                var raw = new Quaternion(snapshot.qx, snapshot.qy, snapshot.qz, snapshot.qw);
                _calibration = Quaternion.Inverse(raw);
                _hasCalibration = true;
            }
        }

        if (pointPrefab == null) return;

        Packet current;
        lock (_lock)
        {
            current = _latest;
        }

        if (current == null) return;

        var q = new Quaternion(current.qx, current.qy, current.qz, current.qw);
        if (_hasCalibration)
        {
            q = _calibration * q;
        }

        var dir = q * Vector3.forward;
        var pos = dir * (current.dist_cm * scaleMeters);

        var point = Instantiate(pointPrefab, pos, Quaternion.identity);
        point.SetParent(transform, false);

        if (transform.childCount > maxPoints)
        {
            Destroy(transform.GetChild(0).gameObject);
        }
    }

        bool IsCalibrationPressed()
        {
    #if ENABLE_INPUT_SYSTEM
        return Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame;
    #else
        return Input.GetKeyDown(KeyCode.Space);
    #endif
        }

    void OnDestroy()
    {
        _running = false;
        _client?.Close();
        if (_thread != null && _thread.IsAlive)
        {
            _thread.Join(500);
        }
    }
}
