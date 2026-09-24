package com.screenmonitor.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.screenmonitor.app.data.AppDatabase
import com.screenmonitor.app.data.AppUsageRow
import com.screenmonitor.app.data.UsageCollector
import com.screenmonitor.app.util.TimeUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** 供各页面使用的稳定色板（按包名哈希取色） */
val AppPalette = listOf(
    Color(0xFF1E88E5), Color(0xFF43A047), Color(0xFFF4511E), Color(0xFF8E24AA),
    Color(0xFF00ACC1), Color(0xFFFB8C00), Color(0xFF3949AB), Color(0xFFD81B60),
    Color(0xFF7CB342), Color(0xFF6D4C41), Color(0xFF546E7A), Color(0xFFC0CA33)
)

fun colorFor(pkg: String): Color =
    AppPalette[Math.floorMod(pkg.hashCode(), AppPalette.size)]

@Composable
fun HomeScreen() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val dao = remember { AppDatabase.get(context).usageDao() }

    var screenMs by remember { mutableStateOf(0L) }
    var rows by remember { mutableStateOf<List<AppUsageRow>>(emptyList()) }
    var loaded by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            UsageCollector.collect(context, dao)
            val today = TimeUtils.today()
            screenMs = dao.totalScreenMs(today) ?: 0L
            rows = dao.appUsageByDate(today)
        }
        loaded = true
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            "今日概览",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(Modifier.height(8.dp))

        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primary
            )
        ) {
            Column(Modifier.fillMaxWidth().padding(20.dp)) {
                Text(
                    "今日亮屏使用时长",
                    color = MaterialTheme.colorScheme.onPrimary,
                    style = MaterialTheme.typography.titleMedium
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    TimeUtils.formatDurationDetail(screenMs),
                    color = MaterialTheme.colorScheme.onPrimary,
                    style = MaterialTheme.typography.displaySmall,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Spacer(Modifier.height(16.dp))
        Text(
            "今日应用使用排行",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )
        Spacer(Modifier.height(8.dp))

        if (!loaded) {
            Text("加载中…", style = MaterialTheme.typography.bodyMedium)
        } else if (rows.isEmpty()) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.fillMaxWidth().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("今天还没有使用记录", style = MaterialTheme.typography.bodyLarge)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "多使用手机一会儿后再来刷新，\n或到「设置」里点立即刷新。",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(rows) { row ->
                    AppUsageRowView(row, maxMs = rows.firstOrNull()?.totalMs ?: 1L)
                }
            }
        }
    }
}

@Composable
fun AppUsageRowView(row: AppUsageRow, maxMs: Long) {
    Card(Modifier.fillMaxWidth()) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier
                    .width(12.dp)
                    .height(12.dp)
                    .background(colorFor(row.pkg), CircleShape)
            )
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(row.appName, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(2.dp))
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .background(MaterialTheme.colorScheme.surfaceVariant, CircleShape)
                ) {
                    Box(
                        Modifier
                            .fillMaxWidth((row.totalMs.toFloat() / maxMs.toFloat()).coerceIn(0f, 1f))
                            .height(6.dp)
                            .background(colorFor(row.pkg), CircleShape)
                    )
                }
            }
            Spacer(Modifier.width(12.dp))
            Text(
                TimeUtils.formatDuration(row.totalMs),
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}
