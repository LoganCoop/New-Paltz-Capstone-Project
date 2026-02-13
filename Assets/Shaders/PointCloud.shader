Shader "Custom/PointCloud"
{
    Properties
    {
        _PointSize ("Point Size", Range(1, 20)) = 5.0
        _Brightness ("Brightness", Range(0, 2)) = 1.0
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100
        
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 5.0
            
            #include "UnityCG.cginc"
            
            struct appdata
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
            };
            
            struct v2f
            {
                float4 vertex : SV_POSITION;
                float4 color : COLOR;
                float psize : PSIZE;
            };
            
            float _PointSize;
            float _Brightness;
            
            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.color = v.color;
                o.psize = _PointSize;
                return o;
            }
            
            fixed4 frag (v2f i) : SV_Target
            {
                return i.color * _Brightness;
            }
            ENDCG
        }
    }
    
    FallBack "Unlit/Color"
}
