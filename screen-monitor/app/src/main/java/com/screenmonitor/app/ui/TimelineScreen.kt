package com.screenmonitor.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.background
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowLeft
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.screenmonitor.app.data.AppDatabase
import com.screenmonitor.app.data.AppSession
import com.screenmonitor.app.data.UsageCollector
import com.screenmonitor.app.util.TimeUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun TimelineScreen() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val dao = remember { AppDatabase.get(context).usageDao() }

    var date by remember { mutableStateOf(TimeUtils.today()) }
    var sessions by remember { mutableStateOf<List<AppSession>>(emptyList()) }
    var screenMs by remember { mutableStateOf(0L) }
    var loaded by remember { mutableStateOf(false) }

    LaunchedEffect(date) {
        withContext(Dispatchers.IO) {
            UsageCollector.collect(context, dao)
            sessions = dao.appSessionsByDate(date)
            screenMs = dao.totalScreenMs(date) ?: 0L
        }
        loaded = true
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = { date = TimeUtils.addDays(date, -1) }) {
                Icon(Icons.AutoMirrored.Filled.KeyboardArrowLeft, contentDescription = "前一天")
            }
            Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    TimeUtils.formatDateCn(TimeUtils.dateToTs(date)),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "亮屏使用 ${TimeUtils.formatDurationDetail(screenMs)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            IconButton(onClick = { date = TimeUtils.addDays(date, 1) }) {
                Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = "后一天")
            }
        }
        if (date != TimeUtils.today()) {
            OutlinedButton(onClick = { date = TimeUtils.today() }) { Text("回到今天") }
        }
        Spacer(Modifier.height(12.dp))

        if (!loaded) {
            Text("加载中…")
        } else if (sessions.isEmpty()) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.fillMaxWidth().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("当天没有应用使用记录", style = MaterialTheme.typography.bodyLarge)
                }
            }
        } else {
            TimelineChart(sessions, date)
            Spacer(Modifier.height(12.dp))
            Text("使用明细", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(sessions) { s ->
                    SessionRow(s)
                }
            }
        }
    }
}

/** 24 小时时间线图：横向色块表示每个应用的使用时段 */
@Composable
fun TimelineChart(sessions: List<AppSession>, date: String) {
    val dayStart = TimeUtils.dateToTs(date)
    val dayMs = 24 * 3600 * 1000L

    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Canvas(
                Modifier
                    .fillMaxWidth()
                    .height(90.dp)
            ) {
                // 小时刻度线
                for (h in 0..24) {
                    val x = h / 24f * size.width
                    drawLine(
                        color = Color(0xFFB0BEC5),
                        start = Offset(x, 0f),
                        end = Offset(x, size.height),
                        strokeWidth = if (h % 6 == 0) 2f else 1f
                    )
                }
                // 使用段色块
                sessions.forEach { s ->
                    val startFrac = ((s.startTs - dayStart).coerceIn(0L, dayMs)) / dayMs.toFloat()
                    val endFrac = ((s.endTs - dayStart).coerceIn(0L, dayMs)) / dayMs.toFloat()
                    val left = startFrac * size.width
                    val right = endFrac * size.width
                    if (right > left + 1f) {
                        drawRect(
                            color = colorFor(s.pkg),
                            topLeft = Offset(left, 6.dp.toPx()),
                            size = Size(right - left, size.height - 24.dp.toPx())
                        )
                    }
                }
                // 底部时间标签
                listOf(0, 6, 12, 18, 24).forEach { h ->
                    val x = h / 24f * size.width
                    drawHourLabel(h.toString().padStart(2, '0'), x, size.height - 6.dp.toPx())
                }
            }
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawHourLabel(
    text: String,
    x: Float,
    baselineY: Float
) {
    val paint = android.graphics.Paint().apply {
        color = android.graphics.Color.parseColor("#78909C")
        textSize = 30f
        textAlign = android.graphics.Paint.Align.CENTER
        isAntiAlias = true
    }
    drawContext.canvas.nativeCanvas.drawText(text, x, baselineY, paint)
}

@Composable
fun SessionRow(s: AppSession) {
    Card(Modifier.fillMaxWidth()) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            androidx.compose.foundation.layout.Box(
                Modifier
                    .width(12.dp)
                    .height(12.dp)
                    .background(colorFor(s.pkg), CircleShape)
            )
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(s.appName, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                Text(
                    "${TimeUtils.formatClock(s.startTs)} - ${TimeUtils.formatClock(s.endTs)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Text(
                TimeUtils.formatDurationDetail(s.durationMs),
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}
