using System;
using System.Collections.Generic;
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
        public Tfluna tfluna;
        public Bno055 bno055;
    }

    [Serializable]
    public class Tfluna
    {
        public double timestamp;
        public float distance_cm;
        public int strength;
        public float temperature_c;
    }

    [Serializable]
    public class Bno055
    {
        public double timestamp;
        public float qw, qx, qy, qz;
    }

    public int port = 5005;
    public Transform pointPrefab;
    public float scaleMeters = 0.01f;
    public float pointScale = 0.02f;
    public int maxPoints = 5000;
    public bool debugOverlay = true;
    public bool ignoreOrientation = false;
    public bool flipX = true;
    public bool flipY = true;
    public Gradient distanceGradient;
    public float minDistanceMeters = 0.1f;
    public float maxDistanceMeters = 5.0f;
    public float minIntensity = 0.2f;
    public float maxIntensity = 1.5f;
    public int minStrength = 100;
    public int distanceMedianWindow = 5;
    [Range(0.0f, 1.0f)] public float orientationSmoothing = 0.5f;
    public float maxTimestampDeltaSeconds = 0.05f;
    public float maxDistanceJumpMeters = 0.15f;

    private UdpClient _client;
    private Thread _thread;
    private bool _running;
    private readonly object _lock = new object();
    private Packet _latest;
    private int _packetCount;
    private long _lastPacketTicks;
    private string _lastSender;

    private Quaternion _calibration = Quaternion.identity;
    private bool _hasCalibration;
    private MaterialPropertyBlock _mpb;
    private static readonly int ColorId = Shader.PropertyToID("_Color");
    private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
    private readonly List<float> _distanceSamples = new List<float>();
    private Quaternion _smoothedOrientation = Quaternion.identity;
    private bool _hasSmoothedOrientation;

    void Start()
    {
        _client = new UdpClient(port);
        _client.Client.ReceiveTimeout = 250;
        _running = true;
        _thread = new Thread(ReceiveLoop) { IsBackground = true };
        _thread.Start();
        _mpb = new MaterialPropertyBlock();
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
                    _packetCount++;
                    _lastPacketTicks = DateTime.UtcNow.Ticks;
                    _lastSender = endPoint.ToString();
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

            if (snapshot != null && snapshot.bno055 != null)
            {
                var raw = new Quaternion(snapshot.bno055.qx, snapshot.bno055.qy, snapshot.bno055.qz, snapshot.bno055.qw);
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

        if (current.tfluna == null || current.bno055 == null) return;

        if (!IsTimestampAligned(current.tfluna.timestamp, current.bno055.timestamp)) return;

        var q = new Quaternion(current.bno055.qx, current.bno055.qy, current.bno055.qz, current.bno055.qw);
        if (_hasCalibration)
        {
            q = _calibration * q;
        }

        if (_hasSmoothedOrientation)
        {
            q = Quaternion.Slerp(_smoothedOrientation, q, orientationSmoothing);
        }
        _smoothedOrientation = q;
        _hasSmoothedOrientation = true;

        if (current.tfluna.strength < minStrength) return;

        var dir = ignoreOrientation ? Vector3.forward : (q * Vector3.forward);
        float rawDistanceMeters = current.tfluna.distance_cm * scaleMeters;
        float filteredDistanceMeters = FilterDistance(rawDistanceMeters);
        if (Mathf.Abs(rawDistanceMeters - filteredDistanceMeters) > maxDistanceJumpMeters) return;

        float distanceMeters = filteredDistanceMeters;
        var pos = dir * distanceMeters;
        if (flipX) pos.x = -pos.x;
        if (flipY) pos.y = -pos.y;

        var point = Instantiate(pointPrefab, pos, Quaternion.identity);
        point.SetParent(transform, false);
        point.localScale = Vector3.one * pointScale;

        ApplyDistanceColor(point, distanceMeters);

        if (transform.childCount > maxPoints)
        {
            Destroy(transform.GetChild(0).gameObject);
        }
    }

    void ApplyDistanceColor(Transform point, float distanceMeters)
    {
        var renderer = point.GetComponent<Renderer>();
        if (renderer == null || distanceGradient == null) return;

        float t = Mathf.InverseLerp(minDistanceMeters, maxDistanceMeters, distanceMeters);
        Color color = distanceGradient.Evaluate(t);
        float intensity = Mathf.Lerp(minIntensity, maxIntensity, t);
        color *= intensity;
        color.a = 1f;

        renderer.GetPropertyBlock(_mpb);
        _mpb.SetColor(ColorId, color);
        _mpb.SetColor(BaseColorId, color);
        renderer.SetPropertyBlock(_mpb);
    }

    float FilterDistance(float distanceMeters)
    {
        int window = Mathf.Max(1, distanceMedianWindow);
        _distanceSamples.Add(distanceMeters);
        if (_distanceSamples.Count > window)
        {
            _distanceSamples.RemoveAt(0);
        }

        if (_distanceSamples.Count == 1) return _distanceSamples[0];

        var temp = _distanceSamples.ToArray();
        System.Array.Sort(temp);
        int mid = temp.Length / 2;
        if (temp.Length % 2 == 1)
        {
            return temp[mid];
        }

        return 0.5f * (temp[mid - 1] + temp[mid]);
    }

    bool IsTimestampAligned(double tflunaTimestamp, double bnoTimestamp)
    {
        if (tflunaTimestamp <= 0 || bnoTimestamp <= 0) return true;
        double delta = Math.Abs(tflunaTimestamp - bnoTimestamp);
        return delta <= maxTimestampDeltaSeconds;
    }

    void OnGUI()
    {
        if (!debugOverlay) return;

        int count;
        long ticks;
        string sender;
        lock (_lock)
        {
            count = _packetCount;
            ticks = _lastPacketTicks;
            sender = _lastSender;
        }

        string lastSeen = ticks == 0
            ? "never"
            : (DateTime.UtcNow - new DateTime(ticks, DateTimeKind.Utc)).TotalSeconds.ToString("0.00") + "s";

        GUI.Label(new Rect(10, 10, 600, 20), "UDP packets: " + count);
        GUI.Label(new Rect(10, 30, 600, 20), "Last packet: " + lastSeen + " ago");
        GUI.Label(new Rect(10, 50, 600, 20), "Last sender: " + (sender ?? "n/a"));
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
